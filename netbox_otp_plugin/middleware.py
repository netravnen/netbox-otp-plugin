from django.http import HttpResponseRedirect
from django.urls import reverse


def normalize_path(path):
    return path.rstrip('/') or '/'


class RedirectToOTPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_path = normalize_path(reverse('login'))
        request_paths = {
            normalize_path(request.path),
            normalize_path(request.path_info),
        }

        if login_path in request_paths:
            redirect_url = reverse('plugins:netbox_otp_plugin:login')
            if request.META.get('QUERY_STRING'):
                redirect_url = f'{redirect_url}?{request.META["QUERY_STRING"]}'
            return HttpResponseRedirect(redirect_url)

        return self.get_response(request)
