import io
import os
import subprocess
import sys
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from apps.cars.models import Brand, Car
from apps.dealerships.models import Dealership
from apps.reports.models import Report

User = get_user_model()

class SecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.u = User.objects.create_user("sec", "sec@x.al", "Str0ng!pass99")

    def test_login_lockout_after_failures(self):
        for _ in range(5):
            r = self.client.post("/en/accounts/login/", {"username": "sec", "password": "wrong"})
            self.assertEqual(r.status_code, 200)
        r = self.client.post("/en/accounts/login/", {"username": "sec", "password": "Str0ng!pass99"})
        self.assertEqual(r.status_code, 429)           # even the right password is refused while locked
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_still_works_normally(self):
        r = self.client.post("/en/accounts/login/", {"username": "sec", "password": "Str0ng!pass99"})
        self.assertEqual(r.status_code, 302)

    def test_signup_rate_limit(self):
        for i in range(10):
            self.client.logout()
            r = self.client.post("/en/accounts/register/", {"username": f"n{i}", "email": f"n{i}@x.al", "password1": "Str0ng!pass99", "password2": "Str0ng!pass99"})
            self.assertEqual(r.status_code, 302, i)
        self.client.logout()
        r = self.client.post("/en/accounts/register/", {"username": "late", "email": "late@x.al", "password1": "Str0ng!pass99", "password2": "Str0ng!pass99"})
        self.assertEqual(r.status_code, 429)
        self.assertFalse(User.objects.filter(username="late").exists())

    def test_report_rate_limit(self):
        b = Brand.objects.get_or_create(name="Audi")[0]
        c = Car.objects.create(owner=self.u, brand=b, model="A", year=2019, price=1, mileage=1, fuel="petrol", transmission="manual",
                               body_type="sedan", color="b", city="T", title="t", description="d", phone="1", status="published")
        for _ in range(12):
            self.client.post(f"/en/reports/{c.slug}/", {"reason": "scam", "message": "x"})
        self.assertEqual(Report.objects.count(), 10)

    def test_dealership_limit_per_user(self):
        self.client.login(username="sec", password="Str0ng!pass99")
        for i in range(4):
            self.client.post("/en/dealerships/new/", {"name": f"D{i}", "city": "T", "phone": "+355691111111"})
        self.assertEqual(Dealership.objects.count(), 3)

    def test_production_refuses_to_start_without_secret_key(self):
        env = {k: v for k, v in os.environ.items() if k not in ("DJANGO_DEBUG", "DJANGO_SECRET_KEY")}
        env["DJANGO_SETTINGS_MODULE"] = "config.settings"
        r = subprocess.run([sys.executable, "-c", "from django.conf import settings; settings.DEBUG"],
                           cwd=str(settings.BASE_DIR), env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", r.stderr)

    def test_debug_is_off_by_default_in_settings(self):
        env = {k: v for k, v in os.environ.items() if k not in ("DJANGO_DEBUG",)}
        env.update(DJANGO_SETTINGS_MODULE="config.settings", DJANGO_SECRET_KEY="x" * 60)
        r = subprocess.run([sys.executable, "-c", "from django.conf import settings; print(settings.DEBUG)"],
                           cwd=str(settings.BASE_DIR), env=env, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "False")

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class UploadPrivacyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.b = Brand.objects.get_or_create(name="Audi")[0]
        User.objects.create_user("up", "up@x.al", "Str0ng!pass99")
        self.client.login(username="up", password="Str0ng!pass99")

    def _data(self, **kw):
        d = dict(brand=self.b.pk, model="A4", year=2018, price=12000, mileage=90000, fuel="diesel", transmission="manual",
                 body_type="sedan", color="Black", condition="used", import_status="imported", city="Tirana",
                 title="Audi A4", description="Clean car", phone="+355691234567")
        d.update(kw); return d

    def test_exif_gps_is_stripped_rotated_and_converted(self):
        im = Image.new("RGB", (40, 20), "orange")
        ex = im.getexif(); ex[0x010F] = "SecretCam"; ex[0x0112] = 6        # Make + Orientation
        gps = ex.get_ifd(0x8825); gps[1] = "N"; gps[2] = (41.0, 19.0, 0.0)  # GPS latitude
        buf = io.BytesIO(); im.save(buf, "JPEG", exif=ex)
        f = SimpleUploadedFile("p.jpg", buf.getvalue(), content_type="image/jpeg")
        r = self.client.post("/en/cars/sell/", {**self._data(), "images": [f]})
        self.assertEqual(r.status_code, 302)
        saved = Car.objects.get().images.get().image
        out = Image.open(saved.path)
        self.assertEqual(out.format, "WEBP")
        self.assertEqual(out.size, (20, 40))                 # rotation applied, then metadata dropped
        self.assertEqual(len(out.getexif()), 0)
        with open(saved.path, "rb") as fh:
            raw = fh.read()
        self.assertNotIn(b"SecretCam", raw)

    def test_huge_text_rejected(self):
        f = SimpleUploadedFile("p.jpg", self._jpeg(), content_type="image/jpeg")
        self.client.post("/en/cars/sell/", {**self._data(description="x" * 5001), "images": [f]})
        self.assertEqual(Car.objects.count(), 0)

    def _jpeg(self):
        b = io.BytesIO(); Image.new("RGB", (20, 20), "red").save(b, "JPEG"); return b.getvalue()

class CspTests(TestCase):
    """Every public page must work with a strict CSP: no inline <script>, no on*= handlers."""
    def setUp(self):
        import re
        self.re = re
        cache.clear()
        self.owner = User.objects.create_user("csp", "csp@x.al", "Str0ng!pass99")
        b = Brand.objects.get_or_create(name="Audi")[0]
        self.car = Car.objects.create(owner=self.owner, brand=b, model="A4", year=2019, price=9000, mileage=1, fuel="petrol",
                                      transmission="manual", body_type="sedan", color="b", city="T", title="t", description="d",
                                      phone="+355691234567", status="published")
        self.d = Dealership.objects.create(name="Dealer", city="T", phone="123"); self.d.users.add(self.owner)

    def _scan(self, url):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, url)
        html = r.content.decode()
        self.assertEqual(self.re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", html), [], "inline script on " + url)
        self.assertEqual(self.re.findall(r"""\son[a-z]+\s*=\s*["']""", html), [], "inline handler on " + url)
        self.assertEqual(self.re.findall(r"javascript:", html), [], "javascript: url on " + url)
        return r

    def test_pages_have_csp_and_no_inline_code(self):
        public = ["/sq/", "/en/", "/sq/cars/", self.car.get_absolute_url(), "/sq/cars/compare/?id=%d" % self.car.pk,
                  "/sq/dealerships/", self.d.get_absolute_url(), "/sq/accounts/login/", "/sq/accounts/register/",
                  "/sq/accounts/password/reset/", "/sq/terms/", "/sq/privacy/", "/sq/reports/%s/" % self.car.slug]
        for url in public:
            r = self._scan(url)
            self.assertIn("script-src 'self'", r["Content-Security-Policy"], url)
            self.assertNotIn("unsafe-eval", r["Content-Security-Policy"])
            self.assertIn("frame-ancestors 'none'", r["Content-Security-Policy"])
            self.assertIn("camera=()", r["Permissions-Policy"])

    def test_logged_in_pages_have_no_inline_code(self):
        self.client.login(username="csp", password="Str0ng!pass99")
        for url in ["/sq/cars/sell/", "/sq/cars/%s/edit/" % self.car.slug, "/sq/accounts/dashboard/", "/sq/accounts/profile/",
                    "/sq/favorites/", "/sq/dealerships/new/", "/sq/dealerships/%s/edit/" % self.d.slug, "/sq/accounts/password/change/"]:
            self._scan(url)

    def test_admin_is_not_given_the_csp(self):
        User.objects.create_superuser("root", "r@x.al", "Str0ng!pass99")
        r = self.client.get("/sq/admin/login/")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Content-Security-Policy", r)

    def test_share_button_has_no_inline_handler(self):
        html = self.client.get(self.car.get_absolute_url()).content.decode()
        self.assertIn("data-share", html)
