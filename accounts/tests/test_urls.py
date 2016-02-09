from __future__ import unicode_literals

import django.test
import django.shortcuts
import django.conf.urls
import django.contrib.admin
import django.core.urlresolvers

import logging


logging.disable(logging.CRITICAL)


urlpatterns = django.conf.urls.patterns(
    '',
    django.conf.urls.url(r'^', django.conf.urls.include('accounts.urls')),
    django.conf.urls.url(r'^admin/', django.conf.urls.include(django.contrib.admin.site.urls)),
)


class UrlsTestCase(django.test.SimpleTestCase):
    urls = 'accounts.tests.test_urls'

    def test_login_urls(self):
        self.assertEqual(
            django.shortcuts.resolve_url('login'), '/login/')
        self.assertEqual(
            django.shortcuts.resolve_url('logout'), '/logout/')

    def test_password_change_urls(self):
        self.assertEqual(
            django.shortcuts.resolve_url('password_change'),
            '/password_change/')
        self.assertEqual(
            django.shortcuts.resolve_url('password_change_done'),
            '/password_change/done/')

    def test_password_reset_urls(self):
        self.assertEqual(
            django.shortcuts.resolve_url('admin_password_reset'),
            '/password_reset/')
        self.assertEqual(
            django.shortcuts.resolve_url(
                'django.contrib.auth.views.password_reset_done'),
            '/password_reset/done/')
        self.assertEqual(
            django.shortcuts.resolve_url(
                'django.contrib.auth.views.password_reset_complete'),
            '/reset/done/')

    def test_masquerade_urls(self):
        self.assertEqual(
            django.shortcuts.resolve_url('end_masquerade'),
            '/admin/masquerade/end/')
        self.assertEqual(
            django.shortcuts.resolve_url('masquerade', user_id=1),
            '/admin/masquerade/1/')
