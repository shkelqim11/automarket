from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.cars.models import Car

class Command(BaseCommand):
    help = "Remove VIP from listings whose vip_until has passed (run daily via cron)."
    def handle(self, *a, **k):
        n = Car.objects.filter(is_vip=True, vip_until__lt=timezone.now()).update(is_vip=False)
        self.stdout.write(f"{n} VIP listings expired")
