from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from apps.cars.models import Car
from .models import Favorite

@login_required
def favorite_list(request):
    favs = Favorite.objects.filter(user=request.user).select_related("car__brand").prefetch_related("car__images")
    return render(request, "dashboard/favorites.html", {"favs": favs})

@login_required
@require_POST
def toggle(request, pk):
    car = get_object_or_404(Car, pk=pk, status=Car.Status.PUBLISHED)
    fav, created = Favorite.objects.get_or_create(user=request.user, car=car)
    if not created:
        fav.delete()
        messages.success(request, _("Removed from favorites."))
    else:
        messages.success(request, _("Saved to favorites."))
    nxt = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        nxt = car.get_absolute_url()
    return redirect(nxt)
