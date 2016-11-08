from __future__ import unicode_literals

import django.forms
from captcha.fields import ReCaptchaField

import models


class CaptchaForm(django.forms.Form):
    captcha = ReCaptchaField()
    username = django.forms.CharField()

    def clean_username(self):
        username = self.cleaned_data.get("username")
        exists = models.User.objects.filter(baseuser_email=username).exists()
        if not exists:
            raise django.forms.ValidationError("Username does not belong to a registered user")
        return username
