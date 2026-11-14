from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from .forms import DealershipForm
from apps.cars.models import Car
from .models import Dealership

def dealer_list(request):
    return render(request, "dealerships/list.html", {"dealers": Dealership.objects.all()})

def dealer_detail(request, slug):
    d = get_object_or_404(Dealership, slug=slug)
    cars = Car.objects.live().filter(dealership=d).select_related("brand").prefetch_related("images")
    return render(request, "dealerships/detail.html", {"d": d, "page": Paginator(cars, 12).get_page(request.GET.get("page"))})


@login_required
def dealer_create(request):
    if request.user.dealerships.count() >= 3:
        messages.error(request, _("You can register at most 3 dealerships."))
        return redirect("dealerships:list")
    form = DealershipForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        d = form.save()
        d.users.add(request.user)
        messages.success(request, _("Dealership created. The verified badge is added by our team after checks."))
        return redirect(d)
    return render(request, "dealerships/form.html", {"form": form})

@login_required
def dealer_edit(request, slug):
    d = get_object_or_404(Dealership, slug=slug)
    if not d.users.filter(pk=request.user.pk).exists():
        raise Http404
    form = DealershipForm(request.POST or None, request.FILES or None, instance=d)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Dealership updated."))
        return redirect(d)
    return render(request, "dealerships/form.html", {"form": form, "d": d})
