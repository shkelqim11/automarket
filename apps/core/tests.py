from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.cars.models import Brand, Car
class T(TestCase):
    def test_home(self):
        u=get_user_model().objects.create_user("a","a@a.al","pw12345!x"); b=Brand.objects.get_or_create(name="Audi")[0]
        Car.objects.create(owner=u,brand=b,model="A4",year=2018,price=9000,mileage=1,fuel="petrol",transmission="manual",body_type="suv",color="b",city="T",title="t",description="d",phone="1",status="published")
        for l in ("sq","en"):
            r=self.client.get(f"/{l}/"); self.assertEqual(r.status_code,200)
        h=self.client.get("/sq/").content.decode()
        for t in ["Të reja sot","Njoftimi i fundit","--ang:","id=\"road\"","rotate(-90 120 120)"]: self.assertIn(t,h,t)

    def test_liquid_glass_assets_render(self):
        h = self.client.get("/sq/").content.decode()
        self.assertIn('<body class="home">', h)
        self.assertIn("liquid-distort", h)
        self.assertIn("glass.css", h)
        h2 = self.client.get("/sq/cars/").content.decode()
        self.assertIn('<body class="">', h2)
        self.assertIn("glass.css", h2)

    def test_seed_brands_idempotent_and_broad(self):
        from django.core.management import call_command
        from apps.cars.models import Brand
        call_command("seed_brands", verbosity=0)
        n = Brand.objects.count()
        self.assertGreaterEqual(n, 130)
        for name in ("Ferrari", "Lamborghini", "BYD", "Yugo", "Zastava", "Lynk & Co"):
            self.assertTrue(Brand.objects.filter(name=name).exists(), name)
        call_command("seed_brands", verbosity=0)
        self.assertEqual(Brand.objects.count(), n)

    def test_brands_exist_after_migrate_and_marquee_prefers_used_brands(self):
        from apps.cars.models import Brand, Car
        self.assertGreaterEqual(Brand.objects.count(), 130)  # seeded by migration
        for slug in ("ferrari", "toyota", "byd"):
            self.assertTrue(Brand.objects.filter(slug=slug).exists(), slug)
        u = get_user_model().objects.create_user("m", "m@m.al", "pw12345!x")
        Car.objects.create(owner=u, brand=Brand.objects.get(name="Yugo"), model="45", year=1990, price=500, mileage=1, fuel="petrol",
                           transmission="manual", body_type="hatchback", color="b", city="T", title="t", description="d", phone="1", status="published")
        names = [b.name for b in self.client.get("/sq/").context["marquee_brands"]]
        self.assertEqual(names[0], "Yugo")  # used brand first, despite being late alphabetically
        self.assertNotIn("Other", names)
