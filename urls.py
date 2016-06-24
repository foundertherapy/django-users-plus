from __future__ import unicode_literals

import django.conf.urls
import django.contrib.admin


urlpatterns = [
    django.conf.urls.url(r'^', django.conf.urls.include('accounts.urls')),
    django.conf.urls.url(r'^admin/', django.conf.urls.include(django.contrib.admin.site.urls)),
]
