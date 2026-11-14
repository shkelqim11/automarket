from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
import uuid

class Brand(models.Model):
    name = models.CharField(_("Brand"), max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *a, **k):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*a, **k)

    def __str__(self):
        return self.name

class CarQuerySet(models.QuerySet):
    def live(self):
        return self.filter(status=Car.Status.PUBLISHED).order_by("-is_vip", "-created_at")

class Car(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PUBLISHED = "published", _("Published")
        REJECTED = "rejected", _("Rejected")
        SOLD = "sold", _("Sold")
    class Fuel(models.TextChoices):
        PETROL = "petrol", _("Petrol")
        DIESEL = "diesel", _("Diesel")
        HYBRID = "hybrid", _("Hybrid")
        ELECTRIC = "electric", _("Electric")
        LPG = "lpg", _("LPG")
    class Transmission(models.TextChoices):
        MANUAL = "manual", _("Manual")
        AUTOMATIC = "automatic", _("Automatic")
    class Body(models.TextChoices):
        SEDAN = "sedan", _("Sedan")
        HATCHBACK = "hatchback", _("Hatchback")
        SUV = "suv", _("SUV")
        WAGON = "wagon", _("Wagon")
        COUPE = "coupe", _("Coupe")
        CONVERTIBLE = "convertible", _("Convertible")
        VAN = "van", _("Van")
        PICKUP = "pickup", _("Pickup")
    class Condition(models.TextChoices):
        NEW = "new", _("New")
        USED = "used", _("Used")
        DAMAGED = "damaged", _("Damaged")
    class ImportStatus(models.TextChoices):
        IMPORTED = "imported", _("Imported")
        NOT_IMPORTED = "not_imported", _("Not imported")
        DUTY_PAID = "duty_paid", _("Customs paid")

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cars")
    dealership = models.ForeignKey("dealerships.Dealership", null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="cars")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="cars", verbose_name=_("Brand"))
    model = models.CharField(_("Model"), max_length=60, db_index=True)
    version = models.CharField(_("Version"), max_length=80, blank=True)
    year = models.PositiveSmallIntegerField(_("Year"), validators=[MinValueValidator(1950), MaxValueValidator(2100)], db_index=True)
    price = models.DecimalField(_("Price (€)"), max_digits=9, decimal_places=0, validators=[MinValueValidator(1)], db_index=True)
    mileage = models.PositiveIntegerField(_("Mileage (km)"), validators=[MaxValueValidator(2_000_000)])
    fuel = models.CharField(_("Fuel"), max_length=10, choices=Fuel.choices, db_index=True)
    transmission = models.CharField(_("Transmission"), max_length=10, choices=Transmission.choices)
    engine_cc = models.PositiveIntegerField(_("Engine size (cc)"), null=True, blank=True)
    power_hp = models.PositiveIntegerField(_("Power (hp)"), null=True, blank=True)
    body_type = models.CharField(_("Body type"), max_length=12, choices=Body.choices)
    color = models.CharField(_("Color"), max_length=30)
    condition = models.CharField(_("Condition"), max_length=10, choices=Condition.choices, default=Condition.USED)
    origin = models.CharField(_("Origin"), max_length=60, blank=True)
    import_status = models.CharField(_("Import status"), max_length=14, choices=ImportStatus.choices, default=ImportStatus.IMPORTED)
    city = models.CharField(_("City"), max_length=60, db_index=True)
    title = models.CharField(_("Listing title"), max_length=120)
    description = models.TextField(_("Description"))
    equipment = models.TextField(_("Equipment"), blank=True, help_text=_("One item per line"))
    phone = models.CharField(_("Phone number"), max_length=25)
    whatsapp = models.CharField(_("WhatsApp"), max_length=25, blank=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    is_vip = models.BooleanField("VIP", default=False)
    vip_until = models.DateTimeField(null=True, blank=True)  # filled when paid VIP launches
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CarQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"]), models.Index(fields=["brand", "model"])]
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0), name="car_price_positive")]

    def save(self, *a, **k):
        if not self.slug:
            base = slugify(f"{self.brand.name} {self.model} {self.year}") or "car"
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        super().save(*a, **k)

    def get_absolute_url(self):
        return reverse("cars:detail", kwargs={"slug": self.slug})

    @property
    def main_image(self):
        imgs = list(self.images.all())
        for i in imgs:
            if i.is_main:
                return i
        return imgs[0] if imgs else None

    @property
    def equipment_list(self):
        return [l.strip() for l in self.equipment.splitlines() if l.strip()]

    @property
    def whatsapp_digits(self):
        return "".join(c for c in (self.whatsapp or self.phone) if c.isdigit())

    def __str__(self):
        return self.title

class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="cars/%Y/%m/")
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_main", "id"]

class ListingView(models.Model):
    """Daily visit statistics per listing."""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="daily_views")
    day = models.DateField(default=timezone.localdate)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("car", "day")]

class VipListing(models.Model):
    """Structure only. Real payments are NOT implemented until a provider for Albania is integrated."""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="vip_records")
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    activated_by_admin = models.BooleanField(default=False)
    note = models.CharField(max_length=200, blank=True)
