import tempfile
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from apps.cars.models import Brand, Car
from apps.core.models import PartnerAd
from .models import Dealership

User = get_user_model()

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DealerTests(TestCase):
    def setUp(self):
        from django.core.cache import cache; cache.clear()
        self.u1 = User.objects.create_user("d1", "d1@x.al", "pass12345!")
        self.u2 = User.objects.create_user("d2", "d2@x.al", "pass12345!")

    def test_create_cannot_self_verify(self):
        self.client.login(username="d1", password="pass12345!")
        r = self.client.post("/en/dealerships/new/", {"name": "Auto Tirana", "city": "Tirana", "phone": "+355691111111", "is_verified": "on"})
        self.assertEqual(r.status_code, 302)
        d = Dealership.objects.get(); self.assertFalse(d.is_verified); self.assertIn(self.u1, d.users.all())

    def test_only_members_edit(self):
        d = Dealership.objects.create(name="X", city="T", phone="123"); d.users.add(self.u1)
        self.client.login(username="d2", password="pass12345!")
        self.assertEqual(self.client.get(f"/en/dealerships/{d.slug}/edit/").status_code, 404)
        self.client.login(username="d1", password="pass12345!")
        self.assertEqual(self.client.get(f"/en/dealerships/{d.slug}/edit/").status_code, 200)

    def test_listing_gets_dealership(self):
        d = Dealership.objects.create(name="X", city="T", phone="123"); d.users.add(self.u1)
        b = Brand.objects.get_or_create(name="Audi")[0]
        c = Car.objects.create(owner=self.u1, dealership=d, brand=b, model="A3", year=2019, price=1, mileage=1, fuel="petrol",
                               transmission="manual", body_type="sedan", color="b", city="T", title="t", description="d", phone="1", status="published")
        self.assertEqual(self.client.get(f"/en/dealerships/{d.slug}/").context["page"][0], c)

    def test_vip_expiry_and_ads(self):
        b = Brand.objects.get_or_create(name="BMW")[0]
        c = Car.objects.create(owner=self.u1, brand=b, model="M3", year=2019, price=1, mileage=1, fuel="petrol", transmission="manual",
                               body_type="sedan", color="b", city="T", title="t", description="d", phone="1", status="published",
                               is_vip=True, vip_until=timezone.now() - timezone.timedelta(days=1))
        call_command("expire_vip"); c.refresh_from_db(); self.assertFalse(c.is_vip)
        self.assertEqual(self.client.get("/en/").status_code, 200)
        PartnerAd.objects.create(title="Insurance", link="https://example.com", active=False, image="ads/x.jpg")
        self.assertNotContains(self.client.get("/en/"), "Insurance")
