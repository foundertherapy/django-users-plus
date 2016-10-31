from __future__ import unicode_literals

import django.forms
from captcha.fields import ReCaptchaField


class CaptchaForm(django.forms.Form):
    captcha = ReCaptchaField()
    username = django.forms.CharField()
