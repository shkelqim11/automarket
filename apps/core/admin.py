from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import render
from django.urls import path
from .models import SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False

# Custom statistics panel at /admin/stats/
_orig_get_urls = admin.site.get_urls
def get_urls():
    def stats(request):
        from apps.cars.models import Car
        from apps.reports.models import Report
        from apps.dealerships.models import Dealership
        ctx = dict(admin.site.each_context(request))
        ctx.update(
            users=get_user_model().objects.count(),
            cars=Car.objects.count(),
            pending=Car.objects.filter(status=Car.Status.PENDING).count(),
            published=Car.objects.filter(status=Car.Status.PUBLISHED).count(),
            sold=Car.objects.filter(status=Car.Status.SOLD).count(),
            vip=Car.objects.filter(is_vip=True).count(),
            open_reports=Report.objects.filter(resolved=False).count(),
            dealerships=Dealership.objects.count(),
            top_brands=Car.objects.values("brand__name").annotate(n=Count("id")).order_by("-n")[:5],
            title="Statistics",
        )
        return render(request, "admin/stats.html", ctx)
    return [path("stats/", admin.site.admin_view(stats), name="stats")] + _orig_get_urls()
admin.site.get_urls = get_urls
admin.site.site_header = "AutoMarket.al"
admin.site.site_title = "AutoMarket.al"
from .models import PartnerAd
admin.site.register(PartnerAd)
