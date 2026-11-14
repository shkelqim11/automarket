from django.urls import path
from . import views
app_name = "cars"
urlpatterns = [
    path("", views.car_list, name="list"),
    path("sell/", views.car_create, name="create"),
    path("compare/", views.compare, name="compare"),
    path("photo/<int:pk>/delete/", views.image_delete, name="image_delete"),
    path("photo/<int:pk>/main/", views.image_main, name="image_main"),
    path("<slug:slug>/", views.car_detail, name="detail"),
    path("<slug:slug>/edit/", views.car_edit, name="edit"),
    path("<slug:slug>/delete/", views.car_delete, name="delete"),
    path("<slug:slug>/sold/", views.car_sold, name="sold"),
]
