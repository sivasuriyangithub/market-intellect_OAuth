from enum import Enum, IntEnum
from io import TextIOWrapper, StringIO
from typing import Optional, List, Iterable, Dict, Iterator, Tuple

import csv
import logging
import requests
import uuid as uuid
import zipfile
from celery import group, chain
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField, ArrayField
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.db.models import F
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from dns import resolver
from google.cloud import storage
from math import ceil
from model_utils.fields import MonitorField
from model_utils.managers import QueryManagerMixin
from model_utils.models import TimeStampedModel, SoftDeletableModel
from requests_cache import CachedSession
from six import BytesIO
from storages.backends.gcloud import GoogleCloudStorage
from tagulous.models import TagField

from whoweb.accounting.ledgers import wkcredits_fulfilled_ledger
from whoweb.accounting.models import Transaction, MatchType
from whoweb.accounting.queries import get_balances_for_object
from whoweb.coldemail.models import ColdEmailTagModel
from whoweb.contrib.fields import CompressedBinaryJSONField
from whoweb.contrib.postgres.fields import EmbeddedModelField
from whoweb.core.models import EventLoggingModel
from whoweb.core.router import router, external_link
from whoweb.payments.exceptions import SubscriptionError
from whoweb.payments.models import WKPlan, BillingAccountMember
from whoweb.search.events import (
    GENERATING_PAGES,
    FINALIZING,
    POST_VALIDATION,
    FETCH_VALIDATION,
    SPAWN_MX,
    POPULATE_DATA,
    FINALIZE_PAGE,
    GENERATING_PAGES_COMPLETE,
    FINALIZING_LOCKED,
    VALIDATION_COMPLETE_LOCKED,
    COMPRESSING_PAGES,
    UPLOAD_TO_BUCKET,
)
from whoweb.users.models import Seat
from .profile import ResultProfile, WORK, PERSONAL, SOCIAL, PROFILE, VALIDATED
from .scroll import FilteredSearchQuery, ScrollSearch

logger = logging.getLogger(__name__)
User = get_user_model()
DATAVALIDATION_URL = "https://dv3.datavalidation.com/api/v2/user/me"


def validation_file_location(instance, filename):
    return f"exports/{instance.uuid.hex}/validate/{filename}"


def download_file_location(instance, filename):
    return f"exports/{instance.uuid.hex}/download/{filename}"


class SearchExportManager(QueryManagerMixin, models.Manager):
    pass


class SearchExport(EventLoggingModel, TimeStampedModel, SoftDeletableModel):
    DERIVATION_RATIO = 3
    PREFETCH_MULTIPLIER = 2
    PAGE_DELAY = 180
    SIMPLE_CAP = 1000
    SKIP_CODE = "MAGIC_SKIP_CODE_NO_VALIDATION_NEEDED"

    ALL_COLUMNS = {
        0: "invitekey",
        1: "Profile ID",
        2: "First Name",
        3: "Last Name",
        4: "Title",
        5: "Company",
        6: "Industry",
        7: "City",
        8: "State",
        9: "Country",
        10: "Email",
        11: "Email Type",
        12: "Email Grade",
        13: "Email 2",
        14: "Email 2 Type",
        15: "Email 2 Grade",
        16: "Email 3",
        17: "Email 3 Type",
        18: "Email 3 Grade",
        19: "Phone Number",
        20: "Phone Number Type",
        21: "Phone Number 2",
        22: "Phone Number 2 Type",
        23: "Phone Number 3",
        24: "Phone Number 3 Type",
        25: "WhoKnows URL",
        26: "LinkedIn URL",
        27: "Facebook",
        28: "Twitter",
        29: "domain",
        30: "mxdomain",
        31: "icebreaker",
    }
    PROFILE_EXCLUDES = {
        "relevance_score",
        "experience",
        "education_history",
        "skills",
        "attenuated_skills",
        "geo_loc",
        "picture_url",
        "picture",
        "seniority_level",
        "time_at_current_company",
        "time_at_current_position",
        "total_experience",
        "business_function",
        "diversity",
        "updated",
    }
    INTRO_COLS = [0]
    BASE_COLS = list(range(1, 10)) + [25]
    DERIVATION_COLS = list(range(10, 25)) + [26, 27, 28]
    UPLOADABLE_COLS = [29, 30, 31]

    EVENT_REVERSE_NAME = "export"

    class ExportStatusOptions(IntEnum):

        CREATED = 0
        PAGES_WORKING = 2
        PAGES_COMPLETE = 4
        VALIDATING = 8
        VALIDATED = 16
        POST_PROCESSED = 32
        COMPLETE = 128

    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, null=True, blank=True)
    billing_seat = models.ForeignKey(
        BillingAccountMember, on_delete=models.CASCADE, null=True, blank=True
    )
    scroll = models.ForeignKey(ScrollSearch, on_delete=models.SET_NULL, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True, blank=True)
    query = EmbeddedModelField(
        FilteredSearchQuery, blank=False, default=FilteredSearchQuery
    )
    pre_validation_file = models.FileField(
        upload_to=validation_file_location, null=True, blank=True, editable=False,
    )
    validation_list_id = models.CharField(max_length=50, null=True, blank=True)
    csv = models.FileField(upload_to=download_file_location, null=True, blank=True)

    status = models.IntegerField(
        _("status"),
        db_index=True,
        choices=[(s.value, s.name) for s in ExportStatusOptions],
        blank=True,
        default=ExportStatusOptions.CREATED,
    )
    status_changed = MonitorField(_("status changed"), monitor="status")
    sent = models.CharField(max_length=255, editable=False)
    sent_at = MonitorField(
        _("sent at"), monitor="sent", editable=False, null=True, default=None
    )
    progress_counter = models.IntegerField(
        default=0, help_text="Number of profiles stored in completed pages"
    )
    target = models.IntegerField(default=0)
    rows_uploaded = models.IntegerField(default=0)

    notify = models.BooleanField(default=False)
    charge = models.BooleanField(default=False)
    uploadable = models.BooleanField(default=False, editable=False)
    extra_columns = JSONField(null=True)

    on_trial = models.BooleanField(default=False)  # ????
    tags = TagField(to=ColdEmailTagModel, blank=True)

    # Managers
    objects = SearchExportManager()
    internal = SearchExportManager(uploadable=True)

    class Meta:
        verbose_name = "export"

    def __str__(self):
        return "%s (%s) %s" % (self.__class__.__name__, self.pk, self.uuid.hex)

    @classmethod
    def create_from_query(
        cls, billing_seat: BillingAccountMember, query: dict, **kwargs
    ):
        """
        :raises SubscriptionError: Billing seat must be subscribed with enough credits to complete the requested export.
        :raises ValidationError: Query must include contact filters for export.
        """
        export = cls(billing_seat=billing_seat, query=query, **kwargs)
        if not export.should_derive_email:
            export.charge = False
        # save here because export needs a pk to be added as evidence to transaction below
        export = export._set_target(save=True)
        if export.charge:
            plan: WKPlan = billing_seat.plan
            if not plan:
                raise SubscriptionError("No plan or subscription found for user.")

            fee_per_row = 0
            filters = export.query.contact_filters
            if not filters:
                raise ValidationError(
                    "An export with derivations must specify contact filters."
                )
            if FilteredSearchQuery.ContactFilterOptions.WORK in filters:
                fee_per_row += plan.credits_per_work_email
            if FilteredSearchQuery.ContactFilterOptions.PERSONAL in filters:
                fee_per_row += plan.credits_per_personal_email
            if FilteredSearchQuery.ContactFilterOptions.PHONE in filters:
                fee_per_row += plan.credits_per_phone
            credits_to_charge = export.target * fee_per_row  # maximum possible
            charged = billing_seat.consume_credits(
                amount=credits_to_charge,
                initiated_by=billing_seat.user,
                evidence=(export,),
            )
            if not charged:
                raise SubscriptionError(
                    f"Not enough credits to complete this export. "
                    f"{billing_seat.credits} available but {credits_to_charge} required"
                )
        return export

    def locked(self, **kwargs):
        return (
            self.__class__.objects.filter(id=self.pk, **kwargs)
            .select_for_update(of=("self",))
            .first()
        )

    def is_done_processing_pages(self):
        if not self.specified_ids and self.should_derive_email:
            target = self.target * self.DERIVATION_RATIO
        else:
            target = self.target
        return (
            int(self.status) >= SearchExport.ExportStatusOptions.PAGES_COMPLETE
            or self.progress_counter >= target
        )

    is_done_processing_pages.boolean = True
    is_done_processing_pages = property(is_done_processing_pages)

    def should_derive_email(self):
        return bool("contact" not in (self.query.defer or []))

    should_derive_email.boolean = True
    should_derive_email.short_description = "Derive Emails"
    should_derive_email = cached_property(should_derive_email)

    def should_remove_derivation_failures(self):
        return len(self.specified_ids) == 0 or self.uploadable

    should_remove_derivation_failures.boolean = True
    should_remove_derivation_failures = cached_property(
        should_remove_derivation_failures
    )

    def defer_validation(self):
        return FilteredSearchQuery.DeferOptions.VALIDATION in self.query.defer

    defer_validation.boolean = True
    defer_validation = cached_property(defer_validation)

    def with_invites(self):
        return bool(self.should_derive_email and self.query.with_invites)

    with_invites.boolean = True
    with_invites = cached_property(with_invites)

    @cached_property
    def skip(self):
        return self.query.filters.skip

    @property
    def specified_ids(self):
        top_level = self.query.filters.profiles
        if top_level:
            return top_level
        if not hasattr(self, "_cached_specified_ids"):
            plus_ids = set()
            minus_ids = set()
            for required in self.query.filters.required:
                if required.field == "_id":
                    if required.truth is True:
                        plus_ids.update(required.value or [])
                    if required.truth is False:
                        minus_ids.update(required.value or [])
            self._cached_specified_ids = list(plus_ids.difference(minus_ids))
        return self._cached_specified_ids

    @specified_ids.setter
    def specified_ids(self, ids):
        self.query.filters.profiles = ids

    @property
    def num_ids_needed(self):
        if not self.specified_ids and self.should_derive_email:
            return int(self.target * self.DERIVATION_RATIO) - self.progress_counter
        else:
            return self.target - self.progress_counter

    @property
    def start_from_count(self):
        progress_plus_skip = self.progress_counter + self.skip
        if not self.specified_ids and self.should_derive_email:
            return int(progress_plus_skip * self.DERIVATION_RATIO)
        else:
            return progress_plus_skip

    @cached_property
    def columns(self):
        if self.with_invites:
            columns = self.INTRO_COLS + self.BASE_COLS + self.DERIVATION_COLS
        elif self.should_derive_email:
            columns = self.BASE_COLS + self.DERIVATION_COLS
        else:
            columns = self.BASE_COLS
        if self.uploadable:
            columns = columns + self.UPLOADABLE_COLS
        return sorted(columns)

    @property
    def charged(self):
        used_credit_ledger = wkcredits_fulfilled_ledger()
        for ledger, balance in get_balances_for_object(self).items():
            if ledger == used_credit_ledger:
                return balance
        return 0

    @property
    def transactions(self):
        return Transaction.objects.filter_by_related_objects(
            (self,), match_type=MatchType.ANY
        )

    def _set_target(self, save=False):
        limit = self.query.filters.limit or 0
        skip = self.query.filters.skip or 0
        initial_query_target = limit - skip
        specified_target = len(self.specified_ids)
        if specified_target > 0:
            initial_query_target = specified_target
        self.target = initial_query_target
        if save:
            self.save()
        return self

    def get_column_names(self):
        if self.uploadable:
            return [
                SearchExport.ALL_COLUMNS[idx].lower().replace(" ", "_")
                for idx in self.columns
            ] + list(self.extra_columns.keys() if self.extra_columns else [])
        else:
            return [SearchExport.ALL_COLUMNS[idx] for idx in self.columns]

    def ensure_search_interface(self, force=False):
        if self.scroll is None:
            search, created = ScrollSearch.get_or_create(
                query=self.query, user_id=self.billing_seat_id
            )
            self.scroll = search
            self.save()
        return self.scroll.ensure_live(force=force)

    def get_raw(self) -> Iterator[ResultProfile]:
        for page in self.pages.filter(data__isnull=False).iterator(chunk_size=1):
            for row in page.data:
                yield row

    def get_raw_by_page(self) -> Iterator[Iterable[ResultProfile]]:
        for page in self.pages.filter(data__isnull=False).iterator(chunk_size=1):
            yield page, page.data

    def get_profiles(self, raw=None) -> Iterator[ResultProfile]:
        if raw is None:
            raw = self.get_raw()
        for profile in raw:
            if profile:
                yield ResultProfile(**profile)

    def get_profiles_by_page(
        self, raw_by_page=None
    ) -> Iterator[Iterator[ResultProfile]]:
        if raw_by_page is None:
            raw_by_page = self.get_raw_by_page()
        for page, page_of_profiles in raw_by_page:
            yield page, self.get_profiles(raw=page_of_profiles)

    def get_ungraded_email_rows(self, profiles=None) -> Iterator[Tuple[str, str]]:
        if profiles is None:
            profiles = self.get_profiles()
        for profile in profiles:
            if profile.passing_grade:
                continue
            profile_id = profile.web_id or profile.id
            graded_emails = set(profile.graded_addresses())
            non_validated_emails = set(profile.emails)
            pending = non_validated_emails.difference(graded_emails)
            for email in pending:
                yield (email, profile_id)

    def generate_email_id_pairs(self, profiles=None) -> Iterator[Tuple[str, str]]:
        if profiles is None:
            profiles = self.get_profiles()
        for profile in profiles:
            if profile.email and profile.id:
                yield (profile.email, profile.id)

    def get_csv_row(
        self, profile: ResultProfile, enforce_valid_contact=False, with_invite=False
    ):
        if enforce_valid_contact:
            if not profile.derivation_status == VALIDATED:
                return
        row = [
            profile.id,
            profile.first_name,
            profile.last_name,
            profile.title,
            profile.company,
            profile.industry,
            profile.city,
            profile.state,
            profile.country,
        ]
        if enforce_valid_contact:
            profile.normalize_email_grades()
            for i in range(3):
                try:
                    entry = profile.graded_emails[i]
                    row.extend(
                        [entry.email, entry.email_type, entry.grade]
                    )  # profile.email_type
                except IndexError:
                    row.extend(["", "", ""])
            for i in range(3):
                try:
                    entry = profile.graded_phones[i]
                    row.extend([entry.number, entry.phone_type])
                except IndexError:
                    row.extend(["", ""])
        row.append(profile.absolute_profile_url)
        if enforce_valid_contact:
            row.extend([profile.li_url, profile.facebook, profile.twitter])
        if with_invite:
            key = profile.get_invite_key(profile.email)
            if not key:
                return
            row = [key] + row
        if self.uploadable:
            row += [
                profile.domain or "",
                profile.mx_domain or "",
                profile.icebreaker or "",
            ] + list(self.extra_columns.values() if self.extra_columns else [])
        return row

    def generate_csv_rows(self, rows: Iterable[ResultProfile] = None):
        if rows is None:
            profiles = self.get_profiles()
        else:
            profiles = rows
        if self.uploadable:
            mx_registry = MXDomain.registry_for_domains(
                domains=(
                    profile.domain
                    for profile in self.get_profiles()  # its ok to get registry for all profiles
                    if profile.domain
                )
            )

            profiles = (profile.set_mx(mx_registry=mx_registry) for profile in profiles)

        yield self.get_column_names()
        count = 0
        for profile in profiles:
            if count >= self.target:
                break
            row = self.get_csv_row(
                profile,
                enforce_valid_contact=self.should_derive_email,
                with_invite=self.with_invites,
            )
            if row is None:
                continue
            count += 1
            yield row

    def generate_json_rows(self, rows=None) -> Iterator[str]:
        return (profile.to_version() for profile in self.get_profiles(raw=rows))

    def compute_charges(self):
        charges = 0
        profiles = self.get_profiles()
        plan: WKPlan = self.billing_seat.plan
        if self.charge:
            return sum(
                plan.compute_contact_credit_use(profile=profile)
                for profile in profiles
                if profile.derivation_status == VALIDATED
            )
        return charges

    def compute_pages_remaining(self):
        search = self.ensure_search_interface()
        if self.specified_ids:
            return 0, 0
        elif (self.num_ids_needed + self.start_from_count) < self.SIMPLE_CAP:
            return 0, 0
        elif self.start_from_count >= search.population():
            return 0, 0
        elif self.num_ids_needed + self.start_from_count > search.population():
            num_ids_needed = search.population() - self.start_from_count
        else:
            num_ids_needed = self.num_ids_needed

        num_pages = int(ceil(float(num_ids_needed) / search.page_size))
        last_completed_page = self.pages.filter(data__isnull=False).last()

        if not last_completed_page:
            start_page = int(ceil(float(self.start_from_count) / search.page_size))
        else:
            start_page = last_completed_page.page_num + 1

        return start_page, num_pages, num_ids_needed

    def _is_scroll_search_or_fetch_ids(
        self,
    ) -> Tuple[bool, Optional[List["SearchExportPage"]]]:
        if self.specified_ids:
            return False, self.specified_ids[self.start_from_count :]
        elif (self.num_ids_needed + self.start_from_count) < self.SIMPLE_CAP:
            search = self.ensure_search_interface()
            return (
                False,
                search.send_simple_search(
                    limit=self.num_ids_needed, skip=self.start_from_count
                ),
            )
        else:
            return True, None

    def _generate_pages_scrolling(
        self, scroller, start_page, num_pages_needed
    ) -> List["SearchExportPage"]:
        pages = []
        # Actual Scrolling
        for page in range(start_page, num_pages_needed + start_page):
            logger.debug("Eagerly fetching page %d of scroll", page)
            profile_ids = scroller.get_ids_for_page(page=page)
            if profile_ids:
                pages.append(SearchExportPage(page_num=page, export=self))
            else:
                break
        return pages

    def _generate_pages_mock_scrolling(
        self, ids, scroller, start_page, num_pages_needed
    ) -> List["SearchExportPage"]:
        pages = []
        for page in range(start_page, num_pages_needed + start_page):
            page_ids = ids[: scroller.page_size]
            scroller.set_web_ids(
                ids=page_ids, page=page
            )  # mock the page results so we don't store ids over and over again
            pages.append(SearchExportPage(page_num=page, export=self))
            ids = ids[scroller.page_size :]
            if len(ids) == 0:
                break
        return pages

    def _compute_num_ids_remaining(self, force_scroller=False) -> int:
        scroller = self.ensure_search_interface(force=force_scroller)
        if self.start_from_count >= scroller.population():
            return 0
        elif self.num_ids_needed + self.start_from_count > scroller.population():
            return scroller.population() - self.start_from_count
        else:
            return self.num_ids_needed

    def _compute_num_pages_remaining(
        self, ids_remaining, force_scroller=False,
    ) -> Tuple[int, int]:
        scroller = self.ensure_search_interface(force=force_scroller)

        num_pages = int(ceil(float(ids_remaining) / scroller.page_size))
        last_completed_page = self.pages.filter(data__isnull=False).last()

        if not last_completed_page:
            start_page = int(ceil(float(self.start_from_count) / scroller.page_size))
        else:
            start_page = last_completed_page.page_num + 1
        return start_page, num_pages

    def _generate_pages(self) -> List["SearchExportPage"]:
        """

        :return: List of export pages for which search cache has been primed.
        :rtype:
        """

        search = self.ensure_search_interface(force=True)
        is_scroll, ids = self._is_scroll_search_or_fetch_ids()

        if is_scroll:
            num_ids_needed = self._compute_num_ids_remaining()
            start_page, num_pages = self._compute_num_pages_remaining(num_ids_needed)
            pages = self._generate_pages_scrolling(
                scroller=search,
                start_page=start_page,
                num_pages_needed=num_pages * self.PREFETCH_MULTIPLIER,
            )
        else:
            num_ids_needed = min(self.num_ids_needed, len(ids))
            start_page, num_pages = self._compute_num_pages_remaining(num_ids_needed)
            pages = self._generate_pages_mock_scrolling(
                ids=ids,
                scroller=search,
                start_page=start_page,
                num_pages_needed=num_pages,
            )
        if pages:
            return SearchExportPage.objects.bulk_create(pages, ignore_conflicts=True)
        return []

    def generate_pages(self, task_context=None) -> List["SearchExportPage"]:
        self.log_event(GENERATING_PAGES, task=task_context)
        with transaction.atomic():
            export = self.locked()
            export.status = SearchExport.ExportStatusOptions.PAGES_WORKING
            export.save()
            pages = export._generate_pages()
            self.log_event(GENERATING_PAGES_COMPLETE, task=task_context)
            return pages

    def get_next_empty_page(self, batch=1) -> Optional["SearchExportPage"]:
        return self.pages.filter(
            data__isnull=True, status=SearchExportPage.PageStatusOptions.CREATED
        )[:batch]

    def compress_working_pages(self, page_ids, task_context=None):
        self.log_event(COMPRESSING_PAGES, task=task_context, data={"pages": page_ids})
        for page in self.pages.filter(pk__in=page_ids):
            page.do_post_derive_process(task_context=task_context)

    @transaction.atomic
    def do_post_pages_completion(self, task_context=None):
        export = self.locked()
        if not export.status <= SearchExport.ExportStatusOptions.PAGES_COMPLETE:
            self.log_event(FINALIZING_LOCKED, task=task_context)
            return False
        export.log_event(FINALIZING, task=task_context)
        if export.charge and not export.defer_validation:
            charges = export.compute_charges()
            credits_to_refund = export.charged - charges
            export.billing_seat.refund_credits(
                amount=credits_to_refund,
                initiated_by=export.billing_seat.user,
                evidence=(export,),
                notes="Computed for inline-validated export at post page completion stage.",
            )
        export.status = SearchExport.ExportStatusOptions.PAGES_COMPLETE
        export.save()
        return True

    @transaction.atomic
    def do_post_validation_completion(self, task_context=None):
        export = self.locked()
        if not export.defer_validation:
            return True
        if not export.status <= SearchExport.ExportStatusOptions.VALIDATED:
            self.log_event(VALIDATION_COMPLETE_LOCKED, task=task_context)
            return False
        results = export.get_validation_results(only_valid=True)
        export.apply_validation_to_profiles_in_pages(validation=results)
        export.status = SearchExport.ExportStatusOptions.VALIDATED
        export.save()
        if export.charge:
            charges = export.compute_charges()
            credits_to_refund = export.charged - charges
            export.billing_seat.refund_credits(
                amount=credits_to_refund,
                initiated_by=export.billing_seat.user,
                evidence=(export,),
                notes="Computed for deferred-validation export at post validation stage.",
            )
        export.return_validation_results_to_cache()
        return True

    def upload_validation(self, task_context=None):
        self.log_event(POST_VALIDATION, task=task_context)
        self.status = SearchExport.ExportStatusOptions.VALIDATING
        try:
            _ = self.get_ungraded_email_rows().__next__()
        except StopIteration:
            # empty
            self.validation_list_id = self.SKIP_CODE
            self.save()
            return

        buffer = StringIO()
        writer = csv.writer(buffer)
        for row in self.get_ungraded_email_rows():
            writer.writerow(row)
        export_file = ContentFile(buffer.getvalue().encode("utf-8"))
        self.pre_validation_file.save(f"wk_validation_{self.uuid.hex}.csv", export_file)
        self.save()

        r = requests.post(
            url=f"{DATAVALIDATION_URL}/list/create_from_url/",
            headers={"Authorization": f"Bearer {settings.DATAVALIDATION_KEY}"},
            data=dict(
                url=self.pre_validation_file.url,
                name=self.uuid.hex,
                email_column_index=0,
                has_header=0,
                start_validation=True,
            ),
        )
        r.raise_for_status()
        self.validation_list_id = r.json()
        self.save()

    def get_validation_status(self, task_context=None):
        if self.validation_list_id == self.SKIP_CODE:
            return True

        self.log_event(FETCH_VALIDATION, task=task_context)

        status = requests.get(
            f"{DATAVALIDATION_URL}/list/{self.validation_list_id}/",
            headers={"Authorization": f"Bearer {settings.DATAVALIDATION_KEY}"},
        ).json()

        if status.get("status_value") == "FAILED":
            return False

        if status.get("status_percent_complete", 0) < 100:
            return False
        r = requests.head(
            f"{DATAVALIDATION_URL}/list/{self.validation_list_id}/download_result/",
            headers={"Authorization": f"Bearer {settings.DATAVALIDATION_KEY}"},
        )
        if not r.ok:
            return False
        s = CachedSession(expire_after=timedelta(days=30).total_seconds())
        r = s.get(
            f"{DATAVALIDATION_URL}/list/{self.validation_list_id}/download_result/",
            headers={"Authorization": f"Bearer {settings.DATAVALIDATION_KEY}"},
            stream=True,
        )
        return r.ok

    def get_validation_results(self, only_valid=True) -> Iterator[Dict]:
        if not self.defer_validation or self.validation_list_id == self.SKIP_CODE:
            return []

        s = CachedSession(
            expire_after=timedelta(days=30).total_seconds(), backend="sqlite"
        )
        r = s.get(
            f"{DATAVALIDATION_URL}/list/{self.validation_list_id}/download_result/",
            headers={"Authorization": f"Bearer {settings.DATAVALIDATION_KEY}"},
            stream=True,
        )
        r.raise_for_status()

        z = zipfile.ZipFile(BytesIO(r.content))

        for name in z.namelist():
            data = z.open(name, "r")
            reader: Iterable[Dict] = csv.DictReader(
                TextIOWrapper(data), fieldnames=("email", "profile_id", "grade")
            )
            try:
                for row in reader:
                    if len(row) != 3:
                        continue
                    if only_valid and row["grade"] not in ["A", "B"]:
                        continue
                    yield row
            except UnicodeDecodeError:
                # not the csv file
                continue

    def make_validation_registry(self, validation_generator: Iterator[Dict]):
        return {grade["email"]: grade["grade"] for grade in validation_generator}

    def apply_validation_to_profiles_in_pages(self, validation):
        registry = self.make_validation_registry(validation_generator=validation)
        for page in self.pages.filter(data__isnull=False).iterator(chunk_size=1):
            profiles = self.get_profiles(raw=page.data)
            page.data = [
                profile.update_validation(registry).dict(
                    exclude=[] if self.uploadable else SearchExport.PROFILE_EXCLUDES
                )
                for profile in profiles
            ]
            page.save()

    def return_validation_results_to_cache(self):
        return router.update_validations(
            json={"from_datavalidation": self.validation_list_id},
            timeout=90,
            request_producer=f"whoweb.search.export/{self.pk}",
        )

    def get_mx_task_group(self):
        from whoweb.search.tasks import fetch_mx_domains

        tasks = []
        for page, page_profiles in self.get_profiles_by_page():
            domains = []
            emails = (
                email
                for email, _ in self.generate_email_id_pairs(profiles=page_profiles)
            )
            for mxd in MXDomain.bulk_from_email(emails):
                domains.append(mxd.pk)
            tasks.append(fetch_mx_domains.si(domains))
        if not tasks:
            return None
        mx_tasks = group(tasks)
        self.log_event(evt=SPAWN_MX)
        return mx_tasks

    def push_to_webhooks(self, rows):
        pass

    def upload_to_static_bucket(
        self, rows: Iterable[ResultProfile] = None, task_context=None
    ):
        self.log_event(UPLOAD_TO_BUCKET, task=task_context)
        buffer = StringIO()
        writer = csv.writer(buffer)
        row_count = 0
        for row in self.generate_csv_rows(rows=rows):
            writer.writerow(row)
            row_count += 1
        export_file = ContentFile(buffer.getvalue().encode("utf-8"))
        if self.uploadable:
            filename = f"{self.uuid.hex}__fetch.csv"
        else:
            filename = f"whoknows_search_results_{self.created.date()}.csv"
        self.csv.save(filename, export_file)
        self.rows_uploaded = row_count
        self.status = self.ExportStatusOptions.COMPLETE
        self.save()
        # Update metadata to ensure download on link-click for users.
        if isinstance(self.csv.storage, GoogleCloudStorage):
            client = storage.Client()
            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            blob_name = self.csv.url.split(settings.GS_BUCKET_NAME + "/", maxsplit=1)[
                -1
            ]
            blob = bucket.get_blob(blob_name)
            blob.content_disposition = "attachment"
            blob.content_type = "text/csv"
            blob.patch()
        return self.csv.url

    @transaction.atomic
    def send_link(self):
        if self.sent:
            return
        if not self.notify:
            return
        export = self.locked()
        if not export:
            return
        if export.sent:
            return
        email = self.billing_seat.seat.email
        link = external_link(self.get_absolute_url())
        json_link = external_link(self.get_absolute_url(filetype="json"))
        subject = "Your WhoKnows Export Results"
        template = "search/download_export.html"
        html_message = render_to_string(
            template_name=template,
            context=dict(
                link=link,
                json_link=json_link,
                graph_url=None,
                tracker=None,
                unsubscribe_link=None,
            ),
        )
        send_mail(
            subject=subject,
            html_message=html_message,
            recipient_list=[email],
            from_email=None,
            message=html_message,
        )
        self.sent = email
        self.save()

    @property
    def queue_priority(self):
        if self.target <= 100:
            return 4
        elif self.target <= 300:
            return 3
        else:
            return 2

    def processing_signatures(self, on_complete=None):
        from whoweb.search.tasks import (
            generate_pages,
            spawn_do_page_process_tasks,
            do_post_pages_completion,
            validate_rows,
            fetch_validation_results,
            send_notification,
            do_post_validation_completion,
            spawn_mx_group,
            upload_to_static_bucket,
        )

        batch_ratio = self.PREFETCH_MULTIPLIER
        if self.specified_ids or batch_ratio == 1:
            do_pages = spawn_do_page_process_tasks.si(
                prefetch_multiplier=1, export_id=self.pk
            )
        else:
            do_pages = chain(
                *[
                    spawn_do_page_process_tasks.si(
                        prefetch_multiplier=1 / 6, export_id=self.pk
                    )
                    for _ in range(6)
                ],
            )

        sigs = (
            generate_pages.si(export_id=self.pk).set(priority=4)
            | do_pages
            | do_post_pages_completion.si(export_id=self.pk).set(priority=3)
        )
        if self.defer_validation:
            sigs |= (
                validate_rows.si(export_id=self.pk)
                | fetch_validation_results.si(export_id=self.pk)
                | do_post_validation_completion.si(export_id=self.pk)
            )
        if self.uploadable:
            sigs |= spawn_mx_group.si(export_id=self.pk)
        if on_complete:
            sigs |= on_complete.clone(kwargs={"export_id": self.pk})
        sigs |= upload_to_static_bucket.si(export_id=self.pk)
        if self.notify:
            sigs |= send_notification.si(export_id=self.pk).set(priority=3)
        return sigs

    def get_absolute_url(self, filetype="csv"):
        if self.status != self.ExportStatusOptions.COMPLETE:
            return
        if filetype == "csv":
            return self.csv.url if self.csv else None
        return reverse(
            "search:download_export", kwargs={"uuid": self.uuid, "filetype": filetype}
        )

    def get_result_rest_url(self):
        if self.status == self.ExportStatusOptions.COMPLETE:
            return reverse("exportresult-detail", args=[self.uuid])


class SearchExportPage(TimeStampedModel):
    export = models.ForeignKey(
        SearchExport, on_delete=models.CASCADE, related_name="pages"
    )

    class PageStatusOptions(IntEnum):
        CREATED = 0
        WORKING = 2
        COMPLETE = 4

    data = CompressedBinaryJSONField(null=True, editable=False)
    page_num = models.PositiveIntegerField()
    working_data = JSONField(editable=False, null=True, default=dict)
    pending_count = models.IntegerField(
        default=0, help_text="Number of tasks enqueued."
    )
    progress_counter = models.IntegerField(
        default=0, help_text="Number of profiles completed and saved."
    )
    count = models.IntegerField(default=0)
    status = models.IntegerField(
        _("status"),
        choices=[(s.value, s.name) for s in PageStatusOptions],
        blank=True,
        default=PageStatusOptions.CREATED,
    )
    status_changed = MonitorField(_("status changed"), monitor="status")

    class Meta:
        unique_together = ["export", "page_num"]
        ordering = ["export", "page_num"]

    @classmethod
    def save_profile(cls, page_pk: int, profile: ResultProfile) -> "SearchExportPage":
        page = cls.objects.get(pk=page_pk)
        if profile.id:
            _, created = WorkingExportRow.objects.update_or_create(
                page=page,
                profile_id=profile.id,
                defaults={
                    "data": profile.dict()
                },  # exclude=SearchExport.PROFILE_EXCLUDES
            )
        else:
            WorkingExportRow.objects.create(
                page=page, data=profile.dict()  # exclude=SearchExport.PROFILE_EXCLUDES
            )
            created = True
        if page:
            page.pending_count = F("pending_count") - int(created)
            page.progress_counter = F("progress_counter") + int(created)
            page.save()
        return page

    def locked(self):
        return (
            self.__class__.objects.filter(id=self.pk)
            .select_for_update(of=("self",))
            .first()
        )

    def _populate_data_directly(self):
        if self.data:
            return
        self.status = SearchExportPage.PageStatusOptions.WORKING
        self.save()
        scroll = self.export.scroll
        ids = scroll.get_ids_for_page(self.page_num)
        profiles = [
            p.dict(exclude=SearchExport.PROFILE_EXCLUDES)
            for p in scroll.get_profiles_for_page(self.page_num)
        ]
        self.count = len(profiles)
        self.data = profiles
        self.status = self.PageStatusOptions.COMPLETE
        self.save()
        # Sometimes search removes duplicate profiles which show up as different ids,
        # in which case we need to push the progress-based skip by the number of dupes.
        adjustment = len(ids) - len(profiles)
        self.export.progress_counter = F("progress_counter") + self.count + adjustment
        self.export.target = F("target") + adjustment
        self.export.save()
        return self.count

    @transaction.atomic
    def populate_data_directly(self, task_context=None):
        self.export.log_event(
            evt=POPULATE_DATA, task=task_context, data={"page": self.page_num}
        )
        page = self.locked()
        return page._populate_data_directly()

    def get_derivation_tasks(self):
        from whoweb.search.tasks import process_derivation_fast, process_derivation_slow

        if self.data:
            return None

        profiles = self.export.scroll.get_profiles_for_page(self.page_num)

        if self.export.defer_validation:
            process_derivation = process_derivation_fast
        else:
            process_derivation = process_derivation_slow

        args = (
            self.export.query.defer,
            self.export.should_remove_derivation_failures,
            self.export.with_invites,
            self.export.query.contact_filters or [WORK, PERSONAL, SOCIAL, PROFILE],
        )
        priority = self.export.queue_priority
        derivation_sigs = [
            process_derivation.si(
                self.pk, profile.dict(exclude=SearchExport.PROFILE_EXCLUDES), *args
            ).set(priority=priority)
            for profile in profiles
        ]
        return derivation_sigs

    def _do_post_derive_process(self) -> [dict]:
        if self.data:
            return []
        profiles = (
            list(self.working_data.values())
            if self.working_data
            else [row.data for row in self.working_rows.all()]
        )
        self.count = len(profiles)
        self.data = profiles
        self.working_data = None
        self.working_rows.all().delete()
        self.pending_count = 0
        self.status = self.PageStatusOptions.COMPLETE
        self.save()
        self.export.progress_counter = F("progress_counter") + self.count
        self.export.save()
        return profiles

    def do_post_derive_process(self, task_context=None):
        self.export.log_event(
            evt=FINALIZE_PAGE, task=task_context, data={"page": self.page_num}
        )
        with transaction.atomic():
            page = self.locked()
            profiles = page._do_post_derive_process()
        self.export.push_to_webhooks(profiles)


class MXDomain(models.Model):
    domain = models.CharField(primary_key=True, max_length=255)
    mxs = ArrayField(models.CharField(max_length=255), default=list)

    @classmethod
    def registry_for_domains(cls, domains):
        instances = cls.objects.filter(domain__in=domains)
        return {instance.domain: instance.mx_domain for instance in instances}

    @classmethod
    def bulk_from_email(cls, emails=()):
        domains = [email.split("@")[1] for email in emails if email]
        return cls.objects.bulk_create(
            [cls(domain=domain) for domain in domains], ignore_conflicts=True
        )

    def fetch_mx(self):
        if self.mxs:
            return
        try:
            answers = resolver.query(self.domain, "MX")
        except (resolver.NXDOMAIN, resolver.NoNameservers):
            # Bad domain.
            return
        except (resolver.NoAnswer, resolver.Timeout):
            # Bad
            return
        self.mxs = [answer.exchange.to_text() for answer in answers]
        self.save()

    @property
    def mx_domain(self):
        try:
            return self.mxs[0]
        except IndexError:
            return None


class WorkingExportRow(models.Model):
    page = models.ForeignKey(
        SearchExportPage, on_delete=models.CASCADE, related_name="working_rows"
    )
    profile_id = models.CharField(max_length=255, blank=True, null=True, default="")
    data = JSONField(default=dict, encoder=DjangoJSONEncoder)
