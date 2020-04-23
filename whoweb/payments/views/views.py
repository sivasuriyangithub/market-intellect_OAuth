import logging

from django.core.exceptions import ValidationError as CoreValidationError
from django.db.models import Q
from django.http import Http404
from djstripe.exceptions import MultipleSubscriptionException
from djstripe.settings import CANCELLATION_AT_PERIOD_END
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from whoweb.contrib.rest_framework.permissions import IsSuperUser
from ..exceptions import PaymentRequired
from ..models import (
    WKPlan,
    WKPlanPreset,
    BillingAccount,
    BillingAccountMember,
)
from ..serializers import (
    PlanSerializer,
    BillingAccountSerializer,
    BillingAccountMemberSerializer,
    PlanPresetSerializer,
    BillingAccountSubscriptionSerializer,
    ManageMemberCreditsSerializer,
)

logger = logging.getLogger(__name__)


class PlanViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    lookup_field = "public_id"
    queryset = WKPlan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsSuperUser]


class PlanPresetViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    serializer_class = PlanPresetSerializer
    permission_classes = [IsSuperUser]
    queryset = WKPlanPreset.objects.all()

    def get_object(self):
        tag_or_public_id = self.kwargs["pk"]
        if not tag_or_public_id:
            raise Http404
        try:
            plan_preset = WKPlanPreset.objects.get(
                Q(tag=tag_or_public_id) | Q(public_id=tag_or_public_id)
            )
        except WKPlanPreset.DoesNotExist:
            raise Http404
        # May raise a permission denied
        self.check_object_permissions(self.request, plan_preset)
        return plan_preset


class BillingAccountViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    lookup_field = "public_id"
    queryset = BillingAccount.objects.all()
    serializer_class = BillingAccountSerializer
    permission_classes = [IsSuperUser]

    request_serializer_class = BillingAccountSerializer
    response_serializer_class = BillingAccountSerializer

    @action(
        detail=True,
        methods=["post", "patch"],
        name="Subscribe",
        request_serializer_class=BillingAccountSubscriptionSerializer,
        url_path="subscription",
    )
    def subscription(self, request, public_id=None):
        billing_account: BillingAccount = self.get_object()
        serializer = BillingAccountSubscriptionSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            if self.request.method == "POST":
                billing_account.subscribe(**serializer.validated_data)
            else:
                billing_account.update_subscription(**serializer.validated_data)
        except MultipleSubscriptionException:
            raise MethodNotAllowed(
                method="POST", detail="Customer already subscribed, use PATCH instead."
            )
        except CoreValidationError as e:
            raise ValidationError(e)
        billing_account.refresh_from_db()
        return Response(
            BillingAccountSerializer(billing_account, context={"request": request}).data
        )

    @subscription.mapping.delete
    def cancel_subscription(self, request, public_id=None):
        billing_account: BillingAccount = self.get_object()
        billing_account.subscription().cancel(at_period_end=CANCELLATION_AT_PERIOD_END)
        return Response(
            BillingAccountSerializer(billing_account, context={"request": request}).data
        )

    @action(
        detail=True,
        methods=["post"],
        name="Set Member Credits",
        request_serializer_class=ManageMemberCreditsSerializer,
    )
    def credits(self, request, pk=None):
        """

        :param request:
        :type request:
        :param pk:
        :type pk:
        :return:
        :rtype:
        """
        billing_account = self.get_object()
        serializer = ManageMemberCreditsSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        member = serializer.validated_data["billing_seat"]
        updated = billing_account.set_member_credits(
            member=member, target=serializer.validated_data["credits"]
        )
        if not updated:
            raise PaymentRequired

        member.refresh_from_db()
        return Response(
            BillingAccountMemberSerializer(member).data, status=status.HTTP_200_OK
        )


class BillingAccountMemberViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    lookup_field = "public_id"
    queryset = BillingAccountMember.objects.all()
    serializer_class = BillingAccountMemberSerializer
    permission_classes = [IsSuperUser]
