from __future__ import unicode_literals

import django.test
import django.test.utils
import django.test.client
from django.conf import settings
import django.contrib.auth.models
import django.core.mail

import logging

from .. import models


logging.disable(logging.CRITICAL)


MIDDLEWARE_CLASSES_NO_DEBUG_TOOLBAR = list(settings.MIDDLEWARE_CLASSES)
if 'debug_toolbar.middleware.DebugToolbarMiddleware' in MIDDLEWARE_CLASSES_NO_DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES_NO_DEBUG_TOOLBAR.remove('debug_toolbar.middleware.DebugToolbarMiddleware')
INSTALLED_APPS_NO_DEBUG_TOOLBAR = list(settings.INSTALLED_APPS)
if 'debug_toolbar' in INSTALLED_APPS_NO_DEBUG_TOOLBAR:
    INSTALLED_APPS_NO_DEBUG_TOOLBAR.remove('debug_toolbar')


@django.test.utils.override_settings(
    MIDDLEWARE_CLASSES=MIDDLEWARE_CLASSES_NO_DEBUG_TOOLBAR,
    INSTALLED_APPS=INSTALLED_APPS_NO_DEBUG_TOOLBAR,
)
class MasqueradeStartTestCase(django.test.TestCase):
    urls = 'accounts.tests.test_urls'
    fixtures = ('test_users.json', 'test_companies.json', 'test_groups.json', )

    def setUp(self):
        self.group_masquerade = django.contrib.auth.models.Group.objects.get(name='Masquerade')
        # make sure masquerade group has masquerade permission
        permission_masquerade = django.contrib.auth.models.Permission.objects.get(codename='masquerade')
        self.group_masquerade.permissions.add(permission_masquerade)

    def test_user_masquerade_admin_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='superuser@example.com', password='password'))
        r = c.get('/admin/masquerade/3/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertTrue(c.session['is_masquerading'])
        self.assertEqual(c.session['masquerade_user_id'], 1)
        self.assertEqual(c.session['return_page'], 'admin:accounts_user_changelist')
        self.assertTrue(c.session['masquerade_is_superuser'])

    def test_staff_masquerade_admin_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='superuser@example.com', password='password'))
        r = c.get('/admin/masquerade/2/')
        self.assertRedirects(r, '/admin/')
        self.assertTrue(c.session['is_masquerading'])
        self.assertEqual(c.session['masquerade_user_id'], 1)
        self.assertEqual(c.session['return_page'], 'admin:accounts_user_changelist')
        self.assertTrue(c.session['masquerade_is_superuser'])

    def test_super_masquerade_admin_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='superuser@example.com', password='password'))
        r = c.get('/admin/masquerade/1/')
        self.assertRedirects(r, '/admin/accounts/user/')
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_user_masquerade_staff_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/3/')
        self.assertRedirects(r, '/admin/accounts/user/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_staff_masquerade_staff_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/2/')
        self.assertRedirects(r, '/admin/accounts/user/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_super_masquerade_staff_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/1/')
        self.assertRedirects(r, '/admin/accounts/user/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_user_masquerade_staff_user(self):
        # give the user masquerade privileges
        u = models.User.objects.get(pk=2)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/3/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertTrue(c.session['is_masquerading'])
        self.assertEqual(c.session['masquerade_user_id'], 2)
        self.assertEqual(c.session['return_page'], 'admin:accounts_user_changelist')
        self.assertFalse(c.session['masquerade_is_superuser'])

    def test_staff_masquerade_staff_user(self):
        # give the user masquerade privileges
        u = models.User.objects.get(pk=2)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/2/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertTrue(c.session['is_masquerading'])
        self.assertEqual(c.session['masquerade_user_id'], 2)
        self.assertEqual(c.session['return_page'], 'admin:accounts_user_changelist')
        self.assertFalse(c.session['masquerade_is_superuser'])

    def test_super_masquerade_staff_user(self):
        # give the user masquerade privileges
        u = models.User.objects.get(pk=2)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/1/')
        self.assertRedirects(r, '/admin/accounts/user/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_user_masquerade_regular_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/3/')
        self.assertRedirects(r, '/admin/accounts/user/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_staff_masquerade_regular_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/2/')
        self.assertRedirects(r, '/admin/accounts/user/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_super_masquerade_regular_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/1/')
        self.assertRedirects(r, '/admin/accounts/user/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_user_masquerade_regular_user(self):
        # give the user masquerade privileges
        u = models.User.objects.get(pk=3)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/3/')
        self.assertRedirects(r, '/admin/accounts/user/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_staff_masquerade_regular_user(self):
        # give the user masquerade privileges
        u = models.User.objects.get(pk=3)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/2/')
        self.assertRedirects(r, '/admin/accounts/user/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_super_masquerade_regular_user(self):
        # give the user masquerade privileges
        u = models.User.objects.get(pk=3)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/1/')
        self.assertRedirects(r, '/admin/accounts/user/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))


@django.test.utils.override_settings(
    MIDDLEWARE_CLASSES=MIDDLEWARE_CLASSES_NO_DEBUG_TOOLBAR,
    INSTALLED_APPS=INSTALLED_APPS_NO_DEBUG_TOOLBAR,
)
class PasswordResetActionTestCase(django.test.TestCase):
    urls = 'accounts.tests.test_urls'
    fixtures = ('test_users.json', 'test_companies.json', 'test_groups.json', )

    def setUp(self):
        group_change_user = django.contrib.auth.models.Group(name='Change User')
        group_change_user.save()
        # make sure masquerade group has masquerade permission
        change_user_permission = django.contrib.auth.models.Permission.objects.get(codename='change_user')
        group_change_user.permissions = [change_user_permission, ]
        u = models.User.objects.get(pk=2)
        u.groups.add(group_change_user)

    def test_password_reset_action_admin_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='superuser@example.com', password='password'))
        r = c.post('/admin/accounts/user/', data={'action': 'reset_passwords', '_selected_action': ['3', '2', ], })
        self.assertRedirects(r, '/admin/accounts/user/')

        # check that we have 2 emails queued up
        self.assertEqual(2, len(django.core.mail.outbox))
        self.assertEqual(django.core.mail.outbox[0].subject, 'Password reset on example.com')
        self.assertEqual(django.core.mail.outbox[1].subject, 'Password reset on example.com')

    def test_password_reset_action_staff_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.post('/admin/accounts/user/', data={'action': 'reset_passwords', '_selected_action': ['3', '2', ], })
        self.assertRedirects(r, '/admin/accounts/user/')

        # check that we have 2 emails queued up
        self.assertEqual(2, len(django.core.mail.outbox))
        self.assertEqual(django.core.mail.outbox[0].subject, 'Password reset on example.com')
        self.assertEqual(django.core.mail.outbox[1].subject, 'Password reset on example.com')

    def test_password_reset_action_regular_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='regularuser@example.com', password='password'))
        r = c.post('/admin/accounts/user/', data={'action': 'reset_passwords', '_selected_action': ['3', '2', ], })
        self.assertRedirects(r, '/admin/login/?next=/admin/accounts/user/')
