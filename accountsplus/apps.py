from __future__ import unicode_literals

from django.apps import AppConfig
import django.contrib.admin


class AccountsConfig(AppConfig):
    name = 'accountsplus'
    verbose_name = "Accounts Plus"

    from accountsplus.forms import EmailBasedAdminAuthenticationForm

    django.contrib.admin.autodiscover()
    django.contrib.admin.site.login_form = EmailBasedAdminAuthenticationForm
