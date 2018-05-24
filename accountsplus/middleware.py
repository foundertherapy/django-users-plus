from __future__ import unicode_literals
import django.utils.timezone
from django.utils.deprecation import MiddlewareMixin
from django.utils import translation


class TimezoneMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if request.user.is_authenticated() and request.user.timezone:
            django.utils.timezone.activate(request.user.timezone)
        else:
            django.utils.timezone.deactivate()


class UserLanguageMiddleware(MiddlewareMixin):

    # Update user preferred language each time a request has a new language and activate translation for that user.
    # Should be added after LocaleMiddleware as it depends on having request.LANGUAGE_CODE configured there.
    def process_request(self, request):
        if hasattr(request, 'user'):
            user = request.user
            if hasattr(user, 'preferred_language'):
                if not user.preferred_language or user.preferred_language != request.LANGUAGE_CODE:
                    user.preferred_language = request.LANGUAGE_CODE
                    user.save()
                else:
                    translation.activate(user.preferred_language)
                    request.LANGUAGE_CODE = translation.get_language()

        lang_in_url = request.GET.get('lang')
        if lang_in_url:
            translation.activate(lang_in_url)
            request.LANGUAGE_CODE = translation.get_language()

