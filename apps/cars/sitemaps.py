from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Car

class CarSitemap(Sitemap):
    i18n = True
    changefreq = "daily"
    def items(self):
        return Car.objects.filter(status=Car.Status.PUBLISHED)
    def lastmod(self, obj):
        return obj.updated_at

class StaticSitemap(Sitemap):
    i18n = True
    def items(self):
        return ["core:home", "cars:list", "dealerships:list"]
    def location(self, item):
        return reverse(item)
