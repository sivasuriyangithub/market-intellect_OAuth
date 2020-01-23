from django.db import models

from whoweb.coldemail.models import CampaignList
from .base import (
    AbstractBaseCampaignRunner,
    AbstractBaseSendingRule,
    AbstractBaseDripRecord,
)
from .metaclass import Messages, Drips


class SimpleSendingRule(AbstractBaseSendingRule):
    manager = models.ForeignKey("SimpleDripCampaignRunner", on_delete=models.CASCADE)


class SimpleDripRecord(AbstractBaseDripRecord):
    manager = models.ForeignKey("SimpleDripCampaignRunner", on_delete=models.CASCADE)


class SimpleDripCampaignRunner(AbstractBaseCampaignRunner):
    """
    This style of campaign is will send the same message to the entire query, up to budget.
    """

    messages = Messages(SimpleSendingRule)
    drips = Drips(SimpleDripRecord)
    use_credits_method = models.CharField(max_length=63, blank=True, null=True)
    open_credit_budget = models.IntegerField()
    preset_campaign_list = models.ForeignKey(
        CampaignList, on_delete=models.CASCADE, null=True
    )

    def create_campaign_list(self, *args, **kwargs):
        if self.preset_campaign_list:
            return self.preset_campaign_list
        return super().create_campaign_list(*args, **kwargs)

    def create_cold_campaign(self, *args, **kwargs):
        if (
            self.campaigns.exists()
        ):  # We only create one. That's what makes it...simple.
            return
        return super().create_cold_campaign(*args, **kwargs)