from datetime import date
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image
import re
from .models import Brand, Car

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleImageField(forms.FileField):
    def __init__(self, *a, **k):
        k.setdefault("widget", MultipleFileInput(attrs={"accept": "image/jpeg,image/png,image/webp", "id": "id_images"}))
        super().__init__(*a, **k)
    def clean(self, data, initial=None):
        single = super().clean
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [single(d, initial) for d in data]

def validate_image(f):
    if f.size > settings.MAX_IMAGE_MB * 1024 * 1024:
        raise ValidationError(_("Each image must be smaller than %(mb)s MB.") % {"mb": settings.MAX_IMAGE_MB})
    try:
        img = Image.open(f)
        if img.width * img.height > 40_000_000:
            raise ValidationError(_("Invalid image file."))
        img.verify()
        fmt = Image.MIME.get(img.format)
    except ValidationError:
        raise
    except Exception:
        raise ValidationError(_("Invalid image file."))
    if fmt not in settings.ALLOWED_IMAGE_TYPES:
        raise ValidationError(_("Only JPG, PNG or WebP images are allowed."))
    f.seek(0)

class CarForm(forms.ModelForm):
    field_order = ["brand", "other_brand"]
    images = MultipleImageField(required=False, label=_("Photos"))
    description = forms.CharField(label=_("Description"), max_length=5000, widget=forms.Textarea(attrs={"rows": 6}))
    equipment = forms.CharField(label=_("Equipment"), max_length=2000, required=False, help_text=_("One item per line"), widget=forms.Textarea(attrs={"rows": 4}))
    other_brand = forms.CharField(required=False, max_length=40, label=_("Other brand (if not listed)"))

    class Meta:
        model = Car
        fields = ["brand", "model", "version", "year", "price", "mileage", "fuel", "transmission",
                  "engine_cc", "power_hp", "body_type", "color", "condition", "origin", "import_status",
                  "city", "title", "description", "equipment", "phone", "whatsapp"]
        widgets = {"description": forms.Textarea(attrs={"rows": 6}), "equipment": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *a, existing_count=0, **k):
        super().__init__(*a, **k)
        self.existing_count = existing_count
        self.fields["brand"].required = False
        self._new_brand_name = None

    def clean_other_brand(self):
        name = " ".join(self.cleaned_data.get("other_brand", "").split())
        if name and not re.fullmatch(r"[\w .&'\-]{2,40}", name):
            raise ValidationError(_("Invalid brand name."))
        return name

    def clean_year(self):
        y = self.cleaned_data["year"]
        if not 1950 <= y <= date.today().year + 1:
            raise ValidationError(_("Enter a valid year."))
        return y

    def clean_phone(self):
        p = self.cleaned_data["phone"].strip()
        digits = [c for c in p if c.isdigit()]
        if len(digits) < 8 or not all(c.isdigit() or c in "+ -()" for c in p):
            raise ValidationError(_("Enter a valid phone number."))
        return p

    def clean_images(self):
        files = self.cleaned_data.get("images") or []
        if len(files) + self.existing_count > settings.MAX_IMAGES_PER_CAR:
            raise ValidationError(_("You can upload at most %(n)s photos.") % {"n": settings.MAX_IMAGES_PER_CAR})
        for f in files:
            validate_image(f)
        return files

    def clean(self):
        data = super().clean()
        other = data.get("other_brand")
        if other and not data.get("brand"):
            existing = Brand.objects.filter(name__iexact=other).first()
            if existing:
                data["brand"] = existing
            else:
                self._new_brand_name = other
        elif not data.get("brand") and not self.errors.get("brand"):
            self.add_error("brand", _("Choose a brand or type it in the other brand field."))
        if not self.instance.pk and self.existing_count + len(data.get("images") or []) == 0:
            self.add_error("images", _("Add at least one photo."))
        return data

def _save_with_brand(self, commit=True):
    if self._new_brand_name:
        brand = Brand.objects.filter(name__iexact=self._new_brand_name).first() or Brand.objects.create(name=self._new_brand_name)
        self.instance.brand = brand
    return forms.ModelForm.save(self, commit=commit)
CarForm.save = _save_with_brand

class CarFilterForm(forms.Form):
    q = forms.CharField(required=False)
    brand = forms.CharField(required=False)
    model = forms.CharField(required=False)
    price_min = forms.IntegerField(required=False, min_value=0)
    price_max = forms.IntegerField(required=False, min_value=0)
    year_min = forms.IntegerField(required=False)
    year_max = forms.IntegerField(required=False)
    km_max = forms.IntegerField(required=False, min_value=0)
    fuel = forms.ChoiceField(required=False, choices=[("", "")] + Car.Fuel.choices)
    transmission = forms.ChoiceField(required=False, choices=[("", "")] + Car.Transmission.choices)
    cc_min = forms.IntegerField(required=False, min_value=0)
    cc_max = forms.IntegerField(required=False, min_value=0)
    hp_min = forms.IntegerField(required=False, min_value=0)
    body_type = forms.ChoiceField(required=False, choices=[("", "")] + Car.Body.choices)
    color = forms.CharField(required=False)
    city = forms.CharField(required=False)
    condition = forms.ChoiceField(required=False, choices=[("", "")] + Car.Condition.choices)
    sort = forms.CharField(required=False)
