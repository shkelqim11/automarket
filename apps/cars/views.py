from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from apps.core.models import SiteSettings
from .forms import CarFilterForm, CarForm
from .images import clean_image
from .models import Brand, Car, CarImage, ListingView

SORTS = {"new": "-created_at", "price_asc": "price", "price_desc": "-price", "year": "-year", "km": "mileage"}

def car_list(request):
    form = CarFilterForm(request.GET)
    qs = Car.objects.live().select_related("brand").prefetch_related("images")
    if form.is_valid():
        d = form.cleaned_data
        for term in d["q"].split():
            qs = qs.filter(Q(title__icontains=term) | Q(model__icontains=term) | Q(version__icontains=term) | Q(brand__name__icontains=term))
        if d["brand"]: qs = qs.filter(brand__slug=d["brand"])
        if d["model"]: qs = qs.filter(model__icontains=d["model"])
        for field, lookup in [("price_min", "price__gte"), ("price_max", "price__lte"), ("year_min", "year__gte"),
                              ("year_max", "year__lte"), ("km_max", "mileage__lte"), ("cc_min", "engine_cc__gte"),
                              ("cc_max", "engine_cc__lte"), ("hp_min", "power_hp__gte")]:
            if d[field] is not None:
                qs = qs.filter(**{lookup: d[field]})
        for f in ("fuel", "transmission", "body_type", "condition"):
            if d[f]: qs = qs.filter(**{f: d[f]})
        if d["color"]: qs = qs.filter(color__icontains=d["color"])
        if d["city"]: qs = qs.filter(city__icontains=d["city"])
        if d["sort"] in SORTS:
            qs = qs.order_by(SORTS[d["sort"]])
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    params = request.GET.copy(); params.pop("page", None)
    return render(request, "cars/list.html", {
        "page": page, "form": form, "sorts": [("new", _("Newest")), ("price_asc", _("Price: low to high")), ("price_desc", _("Price: high to low")), ("year", _("Year")), ("km", _("Mileage"))], "brands": Brand.objects.all(), "qs": params.urlencode(),
        "meta_title": _("Cars for sale") + " | AutoMarket.al",
    })

def car_detail(request, slug):
    car = get_object_or_404(Car.objects.select_related("brand", "owner", "dealership").prefetch_related("images"), slug=slug)
    if car.status in (Car.Status.PENDING, Car.Status.REJECTED) and not (request.user == car.owner or request.user.is_staff):
        raise Http404
    if car.status in (Car.Status.PUBLISHED, Car.Status.SOLD) and request.user != car.owner:
        Car.objects.filter(pk=car.pk).update(views=F("views") + 1)
        lv, _c = ListingView.objects.get_or_create(car=car, day=timezone.localdate())
        ListingView.objects.filter(pk=lv.pk).update(count=F("count") + 1)
    similar = Car.objects.live().filter(Q(brand=car.brand) | Q(body_type=car.body_type)).exclude(pk=car.pk) \
        .select_related("brand").prefetch_related("images")[:4]
    return render(request, "cars/detail.html", {
        "car": car, "similar": similar, "meta_title": f"{car.title} | AutoMarket.al",
        "meta_desc": car.description[:155], "og_image": car.main_image.image.url if car.main_image else None,
    })

def _save_images(car, files):
    has_main = car.images.filter(is_main=True).exists()
    for i, f in enumerate(files):
        CarImage.objects.create(car=car, image=clean_image(f), is_main=(not has_main and i == 0))

@login_required
def car_create(request):
    since = timezone.now() - timezone.timedelta(days=1)
    if Car.objects.filter(owner=request.user, created_at__gte=since).count() >= settings.MAX_LISTINGS_PER_DAY:
        messages.error(request, _("Daily listing limit reached. Try again tomorrow."))
        return redirect("accounts:dashboard")
    form = CarForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        car = form.save(commit=False)
        car.owner = request.user
        dealer = request.user.dealerships.first()
        if dealer: car.dealership = dealer
        car.status = Car.Status.PENDING if SiteSettings.load().require_approval else Car.Status.PUBLISHED
        car.save()
        _save_images(car, form.cleaned_data["images"])
        messages.success(request, _("Listing submitted for approval.") if car.status == Car.Status.PENDING else _("Listing published."))
        return redirect("cars:detail", slug=car.slug)
    return render(request, "cars/form.html", {"form": form, "mode": "create"})

def _own(request, slug):
    car = get_object_or_404(Car, slug=slug)
    if car.owner_id != request.user.id:
        raise Http404
    return car

@login_required
def car_edit(request, slug):
    car = _own(request, slug)
    form = CarForm(request.POST or None, request.FILES or None, instance=car, existing_count=car.images.count())
    if request.method == "POST" and form.is_valid():
        form.save()
        _save_images(car, form.cleaned_data["images"])
        messages.success(request, _("Listing updated."))
        return redirect("cars:detail", slug=car.slug)
    return render(request, "cars/form.html", {"form": form, "car": car, "mode": "edit"})

@login_required
@require_POST
def car_delete(request, slug):
    _own(request, slug).delete()
    messages.success(request, _("Listing deleted."))
    return redirect("accounts:dashboard")

@login_required
@require_POST
def car_sold(request, slug):
    car = _own(request, slug)
    car.status = Car.Status.SOLD
    car.save(update_fields=["status"])
    messages.success(request, _("Marked as sold."))
    return redirect("accounts:dashboard")

@login_required
@require_POST
def image_delete(request, pk):
    img = get_object_or_404(CarImage, pk=pk, car__owner=request.user)
    car, was_main = img.car, img.is_main
    img.delete()
    if was_main and car.images.exists():
        first = car.images.first(); first.is_main = True; first.save()
    messages.success(request, _("Photo deleted."))
    return redirect("cars:edit", slug=car.slug)

@login_required
@require_POST
def image_main(request, pk):
    img = get_object_or_404(CarImage, pk=pk, car__owner=request.user)
    img.car.images.update(is_main=False)
    img.is_main = True; img.save()
    return redirect("cars:edit", slug=img.car.slug)

def car_preview(request):
    """Client-side preview is handled in JS; this endpoint is intentionally absent."""
    raise Http404

def compare(request):
    ids = [i for i in request.GET.getlist("id") if i.isdigit()][:3]
    cars = Car.objects.live().filter(pk__in=ids).select_related("brand").prefetch_related("images")
    return render(request, "cars/compare.html", {"cars": cars})
