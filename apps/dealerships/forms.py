from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.cars.forms import validate_image
from apps.cars.images import clean_image
from .models import Dealership

class DealershipForm(forms.ModelForm):
    class Meta:
        model = Dealership
        fields = ["name", "logo", "description", "city", "address", "phone", "email"]  # is_verified NOT editable
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_logo(self):
        f = self.cleaned_data.get("logo")
        if f and hasattr(f, "content_type"):
            validate_image(f)
            return clean_image(f)
        return f
