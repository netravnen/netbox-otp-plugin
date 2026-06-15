from unittest.mock import Mock, patch

from django.test import RequestFactory
from django.urls import reverse
from utilities.testing import ViewTestCases
from utilities.testing.base import TestCase
from netbox_otp_plugin.models import Device
from netbox_otp_plugin.views import OTPLoginView
from users.models import User


class OTPLoginViewTestCase(TestCase):

    def setUp(self):
        self.view = OTPLoginView()

    @patch('netbox_otp_plugin.views.get_auth_backend_display')
    def test_gen_auth_data_handles_icon_name(self, mock_get_auth_backend_display):
        mock_get_auth_backend_display.return_value = ('GitHub', 'github')

        data = self.view.gen_auth_data('github', '/oauth/login/github/', {'next': '/dcim/'})

        self.assertEqual(data['display_name'], 'GitHub')
        self.assertEqual(data['icon_name'], 'github')
        self.assertIsNone(data['icon_img'])
        self.assertEqual(data['url'], '/oauth/login/github/?next=%2Fdcim%2F')

    @patch('netbox_otp_plugin.views.get_auth_backend_display')
    def test_gen_auth_data_handles_icon_url(self, mock_get_auth_backend_display):
        mock_get_auth_backend_display.return_value = ('Example', 'https://example.com/icon.svg')

        data = self.view.gen_auth_data('example', '/oauth/login/example/', {})

        self.assertEqual(data['display_name'], 'Example')
        self.assertIsNone(data['icon_name'])
        self.assertEqual(data['icon_img'], 'https://example.com/icon.svg')
        self.assertEqual(data['url'], '/oauth/login/example/?')

    def test_redirect_to_next_allows_safe_paths(self):
        request = RequestFactory().get(reverse('plugins:netbox_otp_plugin:login'), {'next': '/dcim/devices/'})
        response = self.view.redirect_to_next(request, Mock())

        self.assertEqual(response.url, '/dcim/devices/')

    def test_redirect_to_next_rejects_unsafe_urls(self):
        request = RequestFactory().get(reverse('plugins:netbox_otp_plugin:login'), {'next': 'https://example.com/'})
        response = self.view.redirect_to_next(request, Mock())

        self.assertEqual(response.url, reverse('home'))


class DeviceTestCase(ViewTestCases.ListObjectsViewTestCase,
                     ViewTestCases.GetObjectViewTestCase,
                     ViewTestCases.DeleteObjectViewTestCase,
                     ViewTestCases.CreateObjectViewTestCase):

    model = Device

    def _get_base_url(self):
        """
        Return the base format for a URL for the test's model. Override this to test for a model which belongs
        to a different app (e.g. testing Interfaces within the virtualization app).
        """
        return '{}:{}:{}_{{}}'.format('plugins', self.model._meta.app_label, self.model._meta.model_name)

    @classmethod
    def setUpTestData(cls):
        users = (
            User(username='user_a'),
            User(username='user_b'),
            User(username='user_c')
        )
        User.objects.bulk_create(users)
        devices = (
            Device(name='device-1', user=users[0]),
            Device(name='device-2', user=users[1])
        )
        Device.objects.bulk_create(devices)

        cls.form_data = {
            'name': 'device-3',
            'user': users[0].pk,
            'digits': 6,
        }

    def test_export_objects(self):
        pass
