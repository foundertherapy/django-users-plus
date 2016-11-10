from __future__ import unicode_literals

import django.forms
from django.conf import settings
from django.apps import apps

from captcha.fields import ReCaptchaField


class CaptchaForm(django.forms.Form):
    captcha = ReCaptchaField()
    username = django.forms.CharField()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        User = apps.get_model(getattr(settings, 'AUTH_USER_MODEL'))
        if not User.objects.filter(email=username).exists():
            raise django.forms.ValidationError("Username does not belong to a registered user")
        return username
