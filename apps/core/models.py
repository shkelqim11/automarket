from django.db import models
from django.utils.translation import gettext_lazy as _

class SiteSettings(models.Model):
    """Singleton: admin decides if listings go live immediately or need approval."""
    require_approval = models.BooleanField(_("Require approval before publishing"), default=True)
    contact_email = models.EmailField(default="info@automarket.al")
    contact_phone = models.CharField(max_length=30, default="+355 69 000 0000")
    address = models.CharField(max_length=200, default="Tiranë, Shqipëri")

    class Meta:
        verbose_name = _("Site settings")
        verbose_name_plural = _("Site settings")

    def save(self, *a, **k):
        self.pk = 1
        super().save(*a, **k)

    @classmethod
    def load(cls):
        obj, _c = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "AutoMarket.al"


class PartnerAd(models.Model):
    """Ad from a partner business. Created and activated manually by an admin (no payment flow)."""
    title = models.CharField(max_length=120)
    image = models.ImageField(upload_to="ads/")
    link = models.URLField()
    active = models.BooleanField(default=False)
    starts_at = models.DateField(null=True, blank=True)
    ends_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title
