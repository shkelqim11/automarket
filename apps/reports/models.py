from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

class Report(models.Model):
    class Reason(models.TextChoices):
        SCAM = "scam", _("Scam or fraud")
        WRONG = "wrong", _("Wrong information")
        DUPLICATE = "duplicate", _("Duplicate listing")
        SOLD = "sold", _("Already sold")
        OTHER = "other", _("Other")
    car = models.ForeignKey("cars.Car", on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    reason = models.CharField(_("Reason"), max_length=12, choices=Reason.choices)
    message = models.TextField(_("Details"), blank=True, max_length=1000)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
