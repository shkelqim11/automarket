from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import include, path
from apps.cars.sitemaps import CarSitemap, StaticSitemap

def robots(request):
    body = "User-agent: *\nDisallow: /*/dashboard/\nSitemap: %s/sitemap.xml\n" % request.build_absolute_uri("/").rstrip("/")
    return HttpResponse(body, content_type="text/plain")

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("robots.txt", robots),
    path("sitemap.xml", sitemap, {"sitemaps": {"cars": CarSitemap, "static": StaticSitemap}}, name="sitemap"),
]
urlpatterns += i18n_patterns(
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("cars/", include("apps.cars.urls")),
    path("dealerships/", include("apps.dealerships.urls")),
    path("favorites/", include("apps.favorites.urls")),
    path("reports/", include("apps.reports.urls")),
    prefix_default_language=True,
)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
