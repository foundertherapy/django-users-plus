from __future__ import unicode_literals

import django.forms
from captcha.fields import ReCaptchaField
from django.conf import settings

class CaptchaForm(django.forms.Form):
    captcha = ReCaptchaField()
    username = django.forms.CharField()

    def clean_username(self):
        username = self.cleaned_data.get("username")
        User = type(getattr(settings, 'AUTH_USER_MODEL'))
        exists = User.objects.filter(baseuser_email=username).exists()
        if not exists:
            raise django.forms.ValidationError("Username does not belong to a registered user")
        return username
