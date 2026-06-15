from utilities.testing.base import TestCase

from django.urls import reverse
from rest_framework import status


class TestRedirectToOTPMiddleware(TestCase):

    def test_login(self):
        url = reverse('login')
        redirect_to = reverse('plugins:netbox_otp_plugin:login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, redirect_to)

    def test_login_preserves_query_string(self):
        url = f'{reverse("login")}?next=/dcim/devices/'
        redirect_to = f'{reverse("plugins:netbox_otp_plugin:login")}?next=/dcim/devices/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, redirect_to)

    def test_login_prefix_not_redirected(self):
        response = self.client.get('/login-extra/')
        self.assertNotEqual(response.status_code, status.HTTP_302_FOUND)

    def test_not_login(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
