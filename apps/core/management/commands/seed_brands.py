from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.cars.brands import BRANDS
from apps.cars.models import Brand


class Command(BaseCommand):
    help = "Create common car brands (safe to run many times; skips existing names/slugs)."

    def handle(self, *args, **opts):
        created = 0
        for name in BRANDS:
            if Brand.objects.filter(name__iexact=name).exists() or Brand.objects.filter(slug=slugify(name)).exists():
                continue
            Brand.objects.create(name=name)
            created += 1
        self.stdout.write(self.style.SUCCESS(f"{created} brands created, {Brand.objects.count()} total"))
