from accountsplus.forms import EmailBasedAdminAuthenticationForm
import django.contrib.admin

__version__ = '1.4.0'

default_app_config = 'accountsplus.apps.AccountsConfig'

django.contrib.admin.autodiscover()
django.contrib.admin.site.login_form = EmailBasedAdminAuthenticationForm
