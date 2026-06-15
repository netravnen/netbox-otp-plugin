import logging

from django.contrib.auth.views import LoginView
from django.contrib.auth import login as auth_login
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.conf import settings
from django.views.decorators.debug import sensitive_post_parameters
from social_core.backends.utils import load_backends
from django.shortcuts import render
from django.contrib.auth.models import update_last_login
from django.contrib.auth.signals import user_logged_in
from django.contrib import messages
from django.http import HttpResponseRedirect

from netbox.authentication import get_auth_backend_display, get_saml_idps
from netbox.config import get_config
from users.models import UserConfig
from netbox.views import generic
from utilities.request import safe_for_redirect
from utilities.string import remove_linebreaks

from . import tables
from . import models
from . import forms


class OTPLoginView(LoginView):
    template_name = 'otp_login.html'
    authentication_form = forms.OTPLoginForm

    @method_decorator(sensitive_post_parameters('password'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def gen_auth_data(self, name, url, params):
        display_name, icon_source = get_auth_backend_display(name)

        icon_name = None
        icon_img = None
        if icon_source:
            if '://' in icon_source:
                icon_img = icon_source
            else:
                icon_name = icon_source

        return {
            'display_name': display_name,
            'icon_name': icon_name,
            'icon_img': icon_img,
            'url': f'{url}?{urlencode(params)}',
        }

    def get_auth_backends(self, request):
        auth_backends = []
        saml_idps = get_saml_idps()

        for name in load_backends(settings.AUTHENTICATION_BACKENDS).keys():
            url = reverse('social:begin', args=[name])
            params = {}
            if next := request.GET.get('next'):
                params['next'] = next
            if name.lower() == 'saml' and saml_idps:
                for idp in saml_idps:
                    params['idp'] = idp
                    data = self.gen_auth_data(name, url, params)
                    data['display_name'] = f'{data["display_name"]} ({idp})'
                    auth_backends.append(data)
            else:
                auth_backends.append(self.gen_auth_data(name, url, params))

        return auth_backends

    def get(self, request):
        form = self.authentication_form(request)

        if request.user.is_authenticated:
            logger = logging.getLogger('netbox.auth.login')
            return self.redirect_to_next(request, logger)
        login_form_hidden = settings.LOGIN_FORM_HIDDEN

        return render(request, self.template_name, {
            'form': form,
            'auth_backends': self.get_auth_backends(request),
            'login_form_hidden': login_form_hidden,
        })

    def post(self, request):
        logger = logging.getLogger('netbox.auth.login')
        form = self.authentication_form(request, data=request.POST)

        if form.is_valid():
            logger.debug("Login form validation was successful")

            # If maintenance mode is enabled, assume the database is read-only, and disable updating the user's
            # last_login time upon authentication.
            if get_config().MAINTENANCE_MODE:
                logger.warning("Maintenance mode enabled: disabling update of most recent login time")
                user_logged_in.disconnect(update_last_login, dispatch_uid='update_last_login')

            # Authenticate user
            auth_login(request, form.get_user())
            logger.info(f"User {request.user} successfully authenticated")
            messages.success(request, _("Logged in as {user}.").format(user=request.user))

            # Ensure the user has a UserConfig defined. (This should normally be handled by
            # create_userconfig() on user creation.)
            if not hasattr(request.user, 'config'):
                request.user.config = get_config()
                UserConfig(user=request.user, data=request.user.config.DEFAULT_USER_PREFERENCES).save()

            response = self.redirect_to_next(request, logger)

            # Set the user's preferred language (if any)
            if language := request.user.config.get('locale.language'):
                response.set_cookie(
                    key=settings.LANGUAGE_COOKIE_NAME,
                    value=language,
                    max_age=request.session.get_expiry_age(),
                    secure=settings.SESSION_COOKIE_SECURE,
                )

            return response

        username = form['username'].value()
        logger.debug(f"Login form validation failed for username: {remove_linebreaks(username)}")

        return render(request, self.template_name, {
            'form': form,
            'auth_backends': self.get_auth_backends(request),
            'login_form_hidden': settings.LOGIN_FORM_HIDDEN,
        })

    def redirect_to_next(self, request, logger):
        data = request.POST if request.method == "POST" else request.GET
        redirect_url = data.get('next', settings.LOGIN_REDIRECT_URL)

        if redirect_url and safe_for_redirect(redirect_url):
            logger.debug(f"Redirecting user to {remove_linebreaks(redirect_url)}")
        else:
            if redirect_url:
                logger.warning(f"Ignoring unsafe 'next' URL passed to login form: {remove_linebreaks(redirect_url)}")
            redirect_url = reverse('home')

        return HttpResponseRedirect(redirect_url)


class DeviceView(generic.ObjectView):
    queryset = models.Device.objects.all()
    template_name = 'otp_device.html'


class DeviceEditView(generic.ObjectEditView):
    queryset = models.Device.objects.all()
    form = forms.DeviceForm


class DeviceDeleteView(generic.ObjectDeleteView):
    queryset = models.Device.objects.all()


class DeviceListView(generic.ObjectListView):
    queryset = models.Device.objects
    table = tables.TOTPDeviceTable
