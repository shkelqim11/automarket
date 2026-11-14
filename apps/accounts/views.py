from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, PasswordResetView
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from apps.cars.models import Car
from apps.core.throttle import client_ip, count, hit, reset
from .forms import ProfileForm, RegisterForm, UserForm

def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegisterForm(request.POST or None)
    ip = client_ip(request)
    if request.method == "POST" and count("signup:" + ip) >= 10:
        form.add_error(None, _("Too many requests. Please try again later."))
        return render(request, "accounts/register.html", {"form": form}, status=429)
    if request.method == "POST" and form.is_valid():
        hit("signup:" + ip, 3600)
        user = form.save()
        login(request, user)
        messages.success(request, _("Welcome to AutoMarket.al!"))
        return redirect("accounts:dashboard")
    return render(request, "accounts/register.html", {"form": form})

@login_required
def dashboard(request):
    cars = Car.objects.filter(owner=request.user).select_related("brand").prefetch_related("images")
    return render(request, "dashboard/index.html", {
        "cars": cars, "total_views": cars.aggregate(s=Sum("views"))["s"] or 0,
        "favorites": request.user.favorites.select_related("car__brand").prefetch_related("car__images"),
    })

@login_required
def profile(request):
    uf = UserForm(request.POST or None, instance=request.user, prefix="u")
    pf = ProfileForm(request.POST or None, instance=request.user.profile, prefix="p")
    if request.method == "POST" and uf.is_valid() and pf.is_valid():
        uf.save(); pf.save()
        messages.success(request, _("Profile updated."))
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"uf": uf, "pf": pf})


class ThrottledLoginView(LoginView):
    """Blocks brute force: 5 failures per IP+username or 20 per IP within 15 minutes."""
    template_name = "accounts/login.html"
    WINDOW = 900

    def _keys(self):
        ip = client_ip(self.request)
        user = (self.request.POST.get("username", "") or "").strip().lower()[:150]
        return "login:%s:%s" % (ip, user), "login-ip:" + ip

    def post(self, request, *args, **kwargs):
        k_user, k_ip = self._keys()
        if count(k_user) >= 5 or count(k_ip) >= 20:
            form = self.get_form()
            form.is_valid()
            form.add_error(None, _("Too many attempts. Try again in 15 minutes."))
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        for k in self._keys():
            hit(k, self.WINDOW)
        return super().form_invalid(form)

    def form_valid(self, form):
        reset(self._keys()[0])
        return super().form_valid(form)

class ThrottledPasswordResetView(PasswordResetView):
    """Limits reset e-mails per IP (e-mail bombing). Over the limit it silently skips sending."""
    def form_valid(self, form):
        ip = client_ip(self.request)
        if count("reset:" + ip) >= 5:
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(self.get_success_url())
        hit("reset:" + ip, 3600)
        return super().form_valid(form)
