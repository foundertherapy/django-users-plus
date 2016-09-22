import logging

import django.test
import django.test.client
import django.utils.timezone

from test_models import (UnitTestCompany, UnitTestUser)


logging.disable(logging.CRITICAL)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class ContextProcessorTestCase(django.test.TestCase):
    @classmethod
    def setUpTestData(cls):
        company_1 = UnitTestCompany.objects.create(name='Example')
        company_2 = UnitTestCompany.objects.create(name='Other Company')

        superuser = UnitTestUser.objects.create_superuser(
            email='superuser@example.com', password='password', first_name='Super', last_name='User')
        superuser.company = company_1
        superuser.save()

        staffuser = UnitTestUser.objects.create_user(
            email='staffuser@example.com', password='password', first_name='Staff', last_name='User', is_staff=True)
        staffuser.company = company_1
        staffuser.save()

        regular_user = UnitTestUser.objects.create_user(
            email='regularuser@example.com', password='password', first_name='Regular', last_name='User')
        regular_user.company = company_1
        regular_user.save()

    def setUp(self):
        self.superuser = UnitTestUser.objects.get(pk=1)

    def test_masquerade_info(self):
        c = django.test.Client()
        response = c.get('/login/')
        self.assertFalse(response.context['is_masquerading'])

        # test that a logged in user also doesn't have is_masquerading
        c.force_login(self.superuser)
        response = c.get('/password_change/')
        self.assertFalse(response.context['is_masquerading'])

        # test that a user that's masquerading DOES indicate so
        response = c.get('/admin/masquerade/3/', follow=True)
        self.assertTrue(response.context['is_masquerading'])

        # test that when a user that's masquerading logs out, the context indicates that
        response = c.get('/admin/masquerade/end/', follow=True)
        self.assertFalse(response.context['is_masquerading'])
