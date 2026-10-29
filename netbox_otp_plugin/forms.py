from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django_otp.forms import OTPAuthenticationFormMixin
from django_otp import devices_for_user, user_has_device

from netbox.forms import NetBoxModelForm
from netbox.plugins import get_plugin_config
from users.models import User
from utilities.forms.fields import DynamicModelChoiceField

from .models import Device


class OTPAuthenticationForm(OTPAuthenticationFormMixin, AuthenticationForm):
    otp_device = forms.CharField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    otp_token = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
                'class': 'rounded'
            }
        ),
        label="OTP Token"
    )
    otp_challenge = forms.CharField(
        required=False
    )

    def clean(self):
        self.cleaned_data = super().clean()
        user = self.get_user()
        otp_required = get_plugin_config('netbox_otp_plugin', 'otp_required')
        if user_has_device(user) or otp_required:
            self.clean_otp(self.get_user())

        return self.cleaned_data

    def _chosen_device(self, user):
        """
        Use the user's only confirmed device when the form names none.

        django-otp 1.7.2 and later no longer try every device of the user
        and require an explicit otp_device. A user with more than one
        device must still choose one from the select field.
        """
        device = super()._chosen_device(user)
        if device is None and not self.cleaned_data.get('otp_device'):
            devices = list(devices_for_user(user, confirmed=True))
            if len(devices) == 1:
                device = devices[0]
        return device

    @property
    def show_device_choices(self):
        # The choices hold a blank entry plus one entry per device.
        return len(self.fields['otp_device'].widget.choices) > 2


class OTPLoginForm(OTPAuthenticationForm):
    pass


class DeviceForm(NetBoxModelForm):
    user = DynamicModelChoiceField(
        label=_('User'),
        queryset=User.objects.all(),
        required=True
    )

    class Meta:
        model = Device
        fields = (
            'name',
            'digits',
            'user',
        )
