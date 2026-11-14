from django.contrib.auth import views as av
from django.urls import path, reverse_lazy
from . import views
app_name = "accounts"
urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.ThrottledLoginView.as_view(), name="login"),
    path("logout/", av.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("password/change/", av.PasswordChangeView.as_view(template_name="accounts/form_page.html",
         success_url=reverse_lazy("accounts:profile")), name="password_change"),
    path("password/reset/", views.ThrottledPasswordResetView.as_view(template_name="accounts/form_page.html",
         email_template_name="accounts/password_reset_email.txt",
         success_url=reverse_lazy("accounts:password_reset_done")), name="password_reset"),
    path("password/reset/done/", av.PasswordResetDoneView.as_view(template_name="accounts/message_page.html"), name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", av.PasswordResetConfirmView.as_view(template_name="accounts/form_page.html",
         success_url=reverse_lazy("accounts:login")), name="password_reset_confirm"),
]
