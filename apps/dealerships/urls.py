from django.urls import path
from . import views
app_name = "dealerships"
urlpatterns = [
    path("", views.dealer_list, name="list"),
    path("new/", views.dealer_create, name="create"),
    path("<slug:slug>/", views.dealer_detail, name="detail"),
    path("<slug:slug>/edit/", views.dealer_edit, name="edit"),
]
