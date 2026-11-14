from django.urls import path
from . import views
app_name = "reports"
urlpatterns = [path("<slug:slug>/", views.report_car, name="create")]
