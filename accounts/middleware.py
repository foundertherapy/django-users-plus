from __future__ import unicode_literals
import django.utils.timezone


class TimezoneMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated() and request.user.timezone:
            django.utils.timezone.activate(request.user.timezone)
        else:
            django.utils.timezone.deactivate()


def show_toolbar(request):
    if request.is_ajax():
        return False

    if request.user.is_superuser:
        return True
    else:
        return False

