from django.test import RequestFactory
from django_otp.oath import totp
from utilities.testing.base import TestCase

from netbox_otp_plugin.forms import OTPLoginForm
from netbox_otp_plugin.models import Device
from users.models import User


class OTPLoginFormTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='otpuser', password='otp-test-password')

    def get_form(self, **data):
        data = {'username': 'otpuser', 'password': 'otp-test-password', **data}
        return OTPLoginForm(request=RequestFactory().post('/'), data=data)

    def test_single_device_needs_no_device_choice(self):
        device = Device.objects.create(user=self.user, name='only')
        form = self.get_form(otp_token=totp(device.bin_key))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user().otp_device.pk, device.pk)

    def test_wrong_token_with_single_device_is_rejected(self):
        Device.objects.create(user=self.user, name='only')
        form = self.get_form(otp_token='000000')

        self.assertFalse(form.is_valid())
        self.assertFalse(form.show_device_choices)

    def test_multiple_devices_need_device_choice(self):
        first = Device.objects.create(user=self.user, name='first')
        Device.objects.create(user=self.user, name='second')
        form = self.get_form(otp_token=totp(first.bin_key))

        self.assertFalse(form.is_valid())
        self.assertTrue(form.show_device_choices)

        form = self.get_form(otp_token=totp(first.bin_key), otp_device=first.persistent_id)
        self.assertTrue(form.is_valid(), form.errors)
