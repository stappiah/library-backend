from django.test import SimpleTestCase
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import Vendor


class FrontendServingTests(SimpleTestCase):
    def test_root_serves_frontend_shell(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Library App")
        self.assertContains(response, "id=\"root\"")

    def test_spa_routes_fall_back_to_frontend_shell(self):
        response = self.client.get("/products/featured")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Library App")

    def test_health_endpoint_reports_backend_ready(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


class VendorApiTests(APITestCase):
    def test_vendor_list_endpoint_is_available(self):
        user = User.objects.create_user(
            username="vendor1",
            email="vendor1@example.com",
            password="testpass123"
        )
        Vendor.objects.create(
            user=user,
            name="University Book Vendor",
            slug="university-book-vendor",
            description="Books sold by a campus vendor"
        )

        response = self.client.get("/api/v1/vendors/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["slug"], "university-book-vendor")
