import io
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
import tempfile
from apps.core.models import SiteSettings
from apps.favorites.models import Favorite
from .models import Brand, Car

User = get_user_model()
TMP = tempfile.mkdtemp()

def img(name="a.jpg", fmt="JPEG", size=(20, 20)):
    b = io.BytesIO(); Image.new("RGB", size, "orange").save(b, fmt)
    return SimpleUploadedFile(name, b.getvalue(), content_type="image/jpeg")

def data(brand, **kw):
    d = dict(brand=brand.pk, model="A4", version="2.0", year=2018, price=12000, mileage=90000, fuel="diesel",
             transmission="manual", engine_cc=1968, power_hp=150, body_type="sedan", color="Black", condition="used",
             origin="Germany", import_status="imported", city="Tirana", title="Audi A4", description="Clean car",
             equipment="ABS\nESP", phone="+355691234567", whatsapp="")
    d.update(kw); return d

@override_settings(MEDIA_ROOT=TMP)
class CarTests(TestCase):
    def setUp(self):
        from django.core.cache import cache; cache.clear()
        self.brand = Brand.objects.get_or_create(name="Audi")[0]
        self.u1 = User.objects.create_user("u1", "u1@x.al", "pass12345!")
        self.u2 = User.objects.create_user("u2", "u2@x.al", "pass12345!")

    def mk(self, owner=None, **kw):
        c = Car.objects.create(owner=owner or self.u1, brand=self.brand, model="A4", year=2018, price=10000, mileage=1000,
                               fuel="diesel", transmission="manual", body_type="sedan", color="Black", city="Tirana",
                               title="t", description="d", phone="+35569123456", status="published", **kw)
        return c

    def test_register_and_login(self):
        r = self.client.post("/en/accounts/register/", {"username": "new", "email": "n@x.al", "password1": "Str0ng!pass99", "password2": "Str0ng!pass99"})
        self.assertEqual(r.status_code, 302)
        self.client.logout()
        self.assertTrue(self.client.login(username="new", password="Str0ng!pass99"))

    def test_sell_requires_login(self):
        r = self.client.get("/en/cars/sell/")
        self.assertEqual(r.status_code, 302)

    def test_create_pending_with_photo(self):
        self.client.login(username="u1", password="pass12345!")
        r = self.client.post("/en/cars/sell/", {**data(self.brand), "images": [img(), img("b.jpg")]})
        self.assertEqual(r.status_code, 302, getattr(r, "context", None) and r.context["form"].errors)
        c = Car.objects.get(); self.assertEqual(c.status, "pending"); self.assertEqual(c.images.count(), 2)
        self.assertTrue(c.images.filter(is_main=True).count() == 1)

    def test_auto_publish_when_no_approval(self):
        SiteSettings.objects.update_or_create(pk=1, defaults={"require_approval": False})
        self.client.login(username="u1", password="pass12345!")
        self.client.post("/en/cars/sell/", {**data(self.brand), "images": [img()]})
        self.assertEqual(Car.objects.get().status, "published")

    def test_rejects_non_image_and_missing_photo(self):
        self.client.login(username="u1", password="pass12345!")
        bad = SimpleUploadedFile("x.jpg", b"not an image", content_type="image/jpeg")
        self.client.post("/en/cars/sell/", {**data(self.brand), "images": [bad]})
        self.assertEqual(Car.objects.count(), 0)
        self.client.post("/en/cars/sell/", data(self.brand))
        self.assertEqual(Car.objects.count(), 0)

    def test_cannot_edit_or_delete_others(self):
        c = self.mk(); self.client.login(username="u2", password="pass12345!")
        self.assertEqual(self.client.get(reverse("cars:edit", args=[c.slug])).status_code, 404)
        self.assertEqual(self.client.post(reverse("cars:delete", args=[c.slug])).status_code, 404)
        self.assertTrue(Car.objects.filter(pk=c.pk).exists())

    def test_owner_edit_delete_sold(self):
        c = self.mk(); self.client.login(username="u1", password="pass12345!")
        r = self.client.post(reverse("cars:edit", args=[c.slug]), {**data(self.brand), "price": 9000})
        self.assertEqual(r.status_code, 302); c.refresh_from_db(); self.assertEqual(c.price, 9000)
        self.client.post(reverse("cars:sold", args=[c.slug])); c.refresh_from_db(); self.assertEqual(c.status, "sold")
        self.client.post(reverse("cars:delete", args=[c.slug])); self.assertFalse(Car.objects.exists())

    def test_filters_and_sort(self):
        self.mk(); c2 = self.mk(); Car.objects.filter(pk=c2.pk).update(price=5000, fuel="petrol")
        r = self.client.get("/en/cars/?fuel=petrol"); self.assertEqual(len(r.context["page"]), 1)
        r = self.client.get("/en/cars/?price_min=6000"); self.assertEqual(len(r.context["page"]), 1)
        r = self.client.get("/en/cars/?sort=price_asc"); self.assertEqual(r.context["page"][0].pk, c2.pk)

    def test_pending_hidden(self):
        c = self.mk(); Car.objects.filter(pk=c.pk).update(status="pending")
        self.assertEqual(self.client.get(c.get_absolute_url()).status_code, 404)
        self.assertEqual(len(self.client.get("/en/cars/").context["page"]), 0)

    def test_favorites(self):
        c = self.mk(); self.client.login(username="u2", password="pass12345!")
        self.client.post(reverse("favorites:toggle", args=[c.pk])); self.assertEqual(Favorite.objects.count(), 1)
        self.client.post(reverse("favorites:toggle", args=[c.pk])); self.assertEqual(Favorite.objects.count(), 0)

    def test_language_switch(self):
        r = self.client.get("/sq/"); self.assertContains(r, "Gjej makinën e ëndrrave të tua.")
        r = self.client.get("/en/"); self.assertContains(r, "Find the car of your dreams.")
        r = self.client.get("/"); self.assertEqual(r.status_code, 302)
        r = self.client.post("/i18n/setlang/", {"language": "en", "next": "/sq/cars/"}); self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("/en/"))

    def test_admin_requires_staff(self):
        self.client.login(username="u1", password="pass12345!")
        r = self.client.get("/en/admin/", follow=False); self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.get("/en/admin/stats/").status_code, 302)
        User.objects.create_superuser("root", "r@x.al", "pass12345!"); self.client.login(username="root", password="pass12345!")
        self.assertEqual(self.client.get("/en/admin/stats/").status_code, 200)

    def test_csrf_enforced(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True); c.login(username="u1", password="pass12345!")
        self.assertEqual(c.post("/en/cars/sell/", data(self.brand)).status_code, 403)

    def test_report_and_sitemap_robots(self):
        c = self.mk(); r = self.client.post(reverse("reports:create", args=[c.slug]), {"reason": "scam", "message": "x"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.get("/sitemap.xml").status_code, 200)
        self.assertContains(self.client.get("/robots.txt"), "Sitemap")

    def test_other_brand_and_multiword_search(self):
        self.client.login(username="u1", password="pass12345!")
        d = {**data(self.brand), "brand": "", "other_brand": "Ferrari", "model": "488 GTB", "title": "Ferrari 488"}
        r = self.client.post("/en/cars/sell/", {**d, "images": [img()]})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Brand.objects.filter(name="Ferrari").exists())
        Car.objects.update(status="published")
        self.assertEqual(len(self.client.get("/en/cars/?q=ferrari 488").context["page"]), 1)
        self.assertEqual(len(self.client.get("/en/cars/?q=ferrari lambo").context["page"]), 0)

    def test_brand_required_one_way_or_other(self):
        self.client.login(username="u1", password="pass12345!")
        self.client.post("/en/cars/sell/", {**data(self.brand), "brand": "", "images": [img()]})
        self.assertEqual(Car.objects.count(), 0)
        self.client.post("/en/cars/sell/", {**data(self.brand), "brand": "", "other_brand": "<script>", "images": [img()]})
        self.assertEqual(Car.objects.count(), 0)
