from django.db import migrations
from django.utils.text import slugify

def seed(apps, schema_editor):
    from apps.cars.brands import BRANDS
    Brand = apps.get_model("cars", "Brand")
    for name in BRANDS:
        if Brand.objects.filter(name__iexact=name).exists() or Brand.objects.filter(slug=slugify(name)).exists():
            continue
        Brand.objects.create(name=name, slug=slugify(name))

class Migration(migrations.Migration):
    dependencies = [("cars", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
