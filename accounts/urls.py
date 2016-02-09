from __future__ import unicode_literals

import django.conf.urls
import django.contrib.admin
import django.contrib.auth.urls
import django.views.generic

import views


urlpatterns = django.conf.urls.patterns(
    '',
    django.conf.urls.url(
        r'^logout/$', views.logout_then_login, name='logout'),
    django.conf.urls.url(
        r'^password_change/$', views.password_change, name='password_change'),
    django.conf.urls.url(
        r'^password_reset/$', views.password_reset, name='password_reset'),
    django.conf.urls.url(
        r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-'
        r'[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        name='password_reset_confirm'),

    # override the admin password reset flow to use the normal site password
    # reset flow
    django.conf.urls.url(
        r'^password_reset/$', views.password_reset,
        name='admin_password_reset'),

    django.conf.urls.url(
        r'^',
        django.conf.urls.include(django.contrib.auth.urls)),

    # masquerade views
    django.conf.urls.url(
        r'^admin/masquerade/end/$', views.end_masquerade,
        name='end_masquerade'),
    django.conf.urls.url(
        r'^admin/masquerade/(?P<user_id>\d+)/$', views.masquerade,
        name='masquerade'),
)
