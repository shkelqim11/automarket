from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

class Dealership(models.Model):
    name = models.CharField(_("Name"), max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    logo = models.ImageField(upload_to="dealers/", blank=True)
    description = models.TextField(_("Description"), blank=True)
    city = models.CharField(_("City"), max_length=60)
    address = models.CharField(_("Address"), max_length=200, blank=True)
    phone = models.CharField(_("Phone number"), max_length=25)
    email = models.EmailField(blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="dealerships", blank=True)
    is_verified = models.BooleanField(_("Verified dealership"), default=False)  # admin only

    class Meta:
        ordering = ["name"]

    def save(self, *a, **k):
        if not self.slug:
            self.slug = slugify(self.name) or "dealer"
            base, n = self.slug, 1
            while Dealership.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                n += 1; self.slug = f"{base}-{n}"
        super().save(*a, **k)

    def get_absolute_url(self):
        return reverse("dealerships:detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class DealerSubscription(models.Model):
    """Structure only. No real payments until a provider for Albania is integrated;
    an admin activates subscriptions manually."""
    class Plan(models.TextChoices):
        BASIC = "basic", _("Basic")
        PRO = "pro", _("Pro")
    dealership = models.ForeignKey(Dealership, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.CharField(max_length=10, choices=Plan.choices, default=Plan.BASIC)
    active = models.BooleanField(default=False)
    starts_at = models.DateField(null=True, blank=True)
    ends_at = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=200, blank=True)
