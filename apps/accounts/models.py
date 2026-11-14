from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(_("Phone number"), max_length=25, blank=True)
    city = models.CharField(_("City"), max_length=60, blank=True)

    def __str__(self):
        return self.user.get_username()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kw):
    if created:
        Profile.objects.get_or_create(user=instance)
