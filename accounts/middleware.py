from __future__ import unicode_literals
import django.utils.timezone


class TimezoneMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated() and request.user.timezone:
            django.utils.timezone.activate(request.user.timezone)
        else:
            django.utils.timezone.deactivate()
