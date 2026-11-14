from django.contrib import admin
from .models import Dealership
@admin.register(Dealership)
class DealershipAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "is_verified"]
    list_editable = ["is_verified"]
    filter_horizontal = ["users"]
    search_fields = ["name", "city"]
from .models import DealerSubscription
admin.site.register(DealerSubscription)
