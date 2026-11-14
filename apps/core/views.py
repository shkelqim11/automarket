from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import render
from apps.cars.models import Brand, Car
from apps.dealerships.models import Dealership
from .models import PartnerAd

def home(request):
    live = Car.objects.live().select_related("brand").prefetch_related("images")
    gauge_frac = max(0.12, min(1.0, Car.objects.filter(status=Car.Status.PUBLISHED).count() / 200))
    ctx = {
        "latest": live[:8],
        "vip_cars": live.filter(is_vip=True)[:4],
        "recommended": live.order_by("-views")[:4],
        "top_brands": Brand.objects.filter(cars__status=Car.Status.PUBLISHED)
                         .annotate(n=Count("cars")).order_by("-n")[:8],
        "dealerships": Dealership.objects.filter(is_verified=True)[:4],
        "ads": PartnerAd.objects.filter(active=True).filter(Q(starts_at__isnull=True) | Q(starts_at__lte=timezone.localdate())).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=timezone.localdate()))[:3],
        "marquee_brands": Brand.objects.annotate(n=Count("cars", filter=Q(cars__status=Car.Status.PUBLISHED))).exclude(name="Other").order_by("-n", "name")[:24],
        "stat_cars": Car.objects.filter(status=Car.Status.PUBLISHED).count(),
        "stat_dealers": Dealership.objects.count(),
        "stat_brands": Brand.objects.count(),
        "brands": Brand.objects.all(),
        "stat_new_today": Car.objects.filter(status=Car.Status.PUBLISHED, created_at__date=timezone.localdate()).count(),
        "gauge_off": "%.1f" % (282.7 * (1 - gauge_frac)),
        "gauge_ang": "%.1f" % (-90 + 180 * gauge_frac),
        "newest": live.order_by("-created_at").first(),
        "meta_title": "AutoMarket.al",
    }
    return render(request, "home.html", ctx)

def terms(request):
    return render(request, "legal.html", {"kind": "terms"})

def privacy(request):
    return render(request, "legal.html", {"kind": "privacy"})
