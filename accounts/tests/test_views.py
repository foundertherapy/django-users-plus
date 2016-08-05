from __future__ import unicode_literals

import django.test
import django.test.utils
import django.test.client
from django.conf import settings
import django.contrib.auth.models
import django.core.mail

import logging

from test_models import (UnitTestCompany, UnitTestUser)
import test_admin


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
    AUTH_USER_MODEL='accounts.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accounts.UnitTestAuditLogEvent',
)
class MasqueradeStartTestCase(django.test.TestCase):
    urls = 'accounts.tests.test_urls'

    @classmethod
    def setUpTestData(cls):
        company_1 = UnitTestCompany.objects.create(name='Example')
        company_2 = UnitTestCompany.objects.create(name='Other Company')

        superuser = UnitTestUser.objects.create_superuser(
            email='superuser@example.com', password='password', first_name='Super', last_name='User')
        superuser.company = company_1
        superuser.save()

        staffuser = UnitTestUser.objects.create_user(
            email='staffuser@example.com', password='password', first_name='Staff', last_name='User')
        staffuser.is_staff = True
        staffuser.company = company_1
        staffuser.save()

        regular_user = UnitTestUser.objects.create_user(
            email='regularuser@example.com', password='password', first_name='Regular', last_name='User')
        regular_user.company = company_1
        regular_user.save()

        group = django.contrib.auth.models.Group.objects.create(name='Masquerade')
        permission_masquerade = django.contrib.auth.models.Permission.objects.get(codename='masquerade')
        group.permissions.add(permission_masquerade)

    def setUp(self):
        self.group_masquerade = django.contrib.auth.models.Group.objects.get(name='Masquerade')

    def test_user_masquerade_admin_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='superuser@example.com', password='password'))
        r = c.get('/admin/masquerade/3/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertTrue(c.session['is_masquerading'])
        self.assertEqual(c.session['masquerade_user_id'], 1)
        self.assertEqual(c.session['return_page'], 'admin:index')
        self.assertTrue(c.session['masquerade_is_superuser'])

    def test_staff_masquerade_admin_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='superuser@example.com', password='password'))
        r = c.get('/admin/masquerade/2/')
        self.assertRedirects(r, '/admin/')
        self.assertTrue(c.session['is_masquerading'])
        self.assertEqual(c.session['masquerade_user_id'], 1)
        self.assertEqual(c.session['return_page'], 'admin:index')
        self.assertTrue(c.session['masquerade_is_superuser'])

    def test_super_masquerade_admin_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='superuser@example.com', password='password'))
        r = c.get('/admin/masquerade/1/')
        self.assertRedirects(r, '/admin/')
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_user_masquerade_staff_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/3/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_staff_masquerade_staff_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/2/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_super_masquerade_staff_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/1/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_user_masquerade_staff_user(self):
        # give the user masquerade privileges
        u = UnitTestUser.objects.get(pk=2)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/3/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertTrue(c.session['is_masquerading'])
        self.assertEqual(c.session['masquerade_user_id'], 2)
        self.assertEqual(c.session['return_page'], 'admin:index')
        self.assertFalse(c.session['masquerade_is_superuser'])

    def test_staff_masquerade_staff_user(self):
        # give the user masquerade privileges
        u = UnitTestUser.objects.get(pk=2)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/2/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertTrue(c.session['is_masquerading'])
        self.assertEqual(c.session['masquerade_user_id'], 2)
        self.assertEqual(c.session['return_page'], 'admin:index')
        self.assertFalse(c.session['masquerade_is_superuser'])

    def test_super_masquerade_staff_user(self):
        # give the user masquerade privileges
        u = UnitTestUser.objects.get(pk=2)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/1/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_user_masquerade_regular_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/3/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_staff_masquerade_regular_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/2/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_super_masquerade_regular_user_no_perm(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/1/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_user_masquerade_regular_user(self):
        # give the user masquerade privileges
        u = UnitTestUser.objects.get(pk=3)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/3/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_staff_masquerade_regular_user(self):
        # give the user masquerade privileges
        u = UnitTestUser.objects.get(pk=3)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/2/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))

    def test_super_masquerade_regular_user(self):
        # give the user masquerade privileges
        u = UnitTestUser.objects.get(pk=3)
        u.groups.add(self.group_masquerade)
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.get('/admin/masquerade/1/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        self.assertIsNone(c.session.get('is_masquerading'))
        self.assertIsNone(c.session.get('masquerade_user_id'))
        self.assertIsNone(c.session.get('return_page'))
        self.assertIsNone(c.session.get('masquerade_is_superuser'))


@django.test.utils.override_settings(
    MIDDLEWARE_CLASSES=MIDDLEWARE_CLASSES_NO_DEBUG_TOOLBAR,
    INSTALLED_APPS=INSTALLED_APPS_NO_DEBUG_TOOLBAR,
    AUTH_USER_MODEL='accounts.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accounts.UnitTestAuditLogEvent',
)
class PasswordResetActionTestCase(django.test.TestCase):
    urls = 'accounts.tests.test_urls'

    @classmethod
    def setUpTestData(cls):
        company_1 = UnitTestCompany.objects.create(name='Example')
        company_2 = UnitTestCompany.objects.create(name='Other Company')

        superuser = UnitTestUser.objects.create_superuser(
            email='superuser@example.com', password='password', first_name='Super', last_name='User')
        superuser.company = company_1
        superuser.save()

        staffuser = UnitTestUser.objects.create_user(
            email='staffuser@example.com', password='password', first_name='Staff', last_name='User')
        staffuser.is_staff = True
        staffuser.company = company_1
        staffuser.save()

        regular_user = UnitTestUser.objects.create_user(
            email='regularuser@example.com', password='password', first_name='Regular', last_name='User')
        regular_user.company = company_1
        regular_user.save()

        group = django.contrib.auth.models.Group.objects.create(name='Masquerade')
        permission_masquerade = django.contrib.auth.models.Permission.objects.get(codename='masquerade')
        group.permissions.add(permission_masquerade)

    def setUp(self):
        group_change_user = django.contrib.auth.models.Group(name='Change User')
        group_change_user.save()
        # make sure masquerade group has masquerade permission
        change_user_permission = django.contrib.auth.models.Permission.objects.get(codename='change_user')
        group_change_user.permissions = [change_user_permission, ]
        u = UnitTestUser.objects.get(pk=2)
        u.groups.add(group_change_user)

    def test_password_reset_action_admin_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='superuser@example.com', password='password'))
        r = c.post('/admin/accounts/unittestuser/', data={'action': 'reset_passwords', '_selected_action': ['3', '2', ], })
        self.assertRedirects(r, '/admin/accounts/unittestuser/')

        # check that we have 2 emails queued up
        self.assertEqual(2, len(django.core.mail.outbox))
        self.assertEqual(django.core.mail.outbox[0].subject, 'Password reset on example.com')
        self.assertEqual(django.core.mail.outbox[1].subject, 'Password reset on example.com')

    def test_password_reset_action_staff_user_no_permission(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))

        # test that a staff user without change permission can't reset a password
        r = c.post('/admin/accounts/unittestuser/', data={'action': 'reset_passwords', '_selected_action': ['3', '2', ], })
        self.assertEqual(r.status_code, 403)

    def test_password_reset_action_staff_user_with_permission(self):
        c = django.test.client.Client()
        # give the staffuser the permission to change users so that it can send a password reset
        staffuser = UnitTestUser.objects.get(email='staffuser@example.com')
        staffuser.user_permissions.add(django.contrib.auth.models.Permission.objects.get(codename='change_unittestuser'))

        # test that a staff user with change permission can reset a password
        self.assertTrue(c.login(email='staffuser@example.com', password='password'))
        r = c.post('/admin/accounts/unittestuser/', data={'action': 'reset_passwords', '_selected_action': ['3', '2', ], })
        self.assertRedirects(r, '/admin/accounts/unittestuser/')

        # check that we have 2 emails queued up
        self.assertEqual(2, len(django.core.mail.outbox))
        self.assertEqual(django.core.mail.outbox[0].subject, 'Password reset on example.com')
        self.assertEqual(django.core.mail.outbox[1].subject, 'Password reset on example.com')


    def test_password_reset_action_regular_user(self):
        c = django.test.client.Client()
        self.assertTrue(c.login(email='regularuser@example.com', password='password'))
        r = c.post('/admin/accounts/unittestuser/', data={'action': 'reset_passwords', '_selected_action': ['3', '2', ], })
        self.assertRedirects(r, '/admin/login/?next=/admin/accounts/unittestuser/')
