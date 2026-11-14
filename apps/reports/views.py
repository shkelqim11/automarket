from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from apps.cars.models import Car
from apps.core.throttle import client_ip, count, hit
from .models import Report

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}

def report_car(request, slug):
    car = get_object_or_404(Car, slug=slug)
    form = ReportForm(request.POST or None)
    ip = client_ip(request)
    if request.method == "POST" and count("report:" + ip) >= 10:
        messages.error(request, _("Too many requests. Please try again later."))
        return redirect(car.get_absolute_url())
    if request.method == "POST" and form.is_valid():
        hit("report:" + ip, 3600)
        r = form.save(commit=False)
        r.car = car
        r.reporter = request.user if request.user.is_authenticated else None
        r.save()
        messages.success(request, _("Thank you. Our team will review the report."))
        return redirect(car.get_absolute_url())
    return render(request, "accounts/form_page.html", {"form": form, "title": _("Report listing"), "submit": _("Send report")})
