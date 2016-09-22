from __future__ import unicode_literals

import django.test
import django.core.mail
import django.db.models
import django.conf

import logging

from .. import models


logging.disable(logging.CRITICAL)


class UnitTestCompany(models.BaseCompany):
    bar = django.db.models.CharField(max_length=100)


class UnitTestUser(models.BaseUser):
    foo = django.db.models.CharField(max_length=100)
    company = django.db.models.ForeignKey('UnitTestCompany', null=True, related_name='users')


class UnitTestAuditLogEvent(models.BaseAuditLogEvent):
    baz = django.db.models.CharField(max_length=100)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
)
class UserManagerTestCase(django.test.TestCase):
    @classmethod
    def setUpTestData(cls):
        company_1 = UnitTestCompany.objects.create(name='Example')
        company_2 = UnitTestCompany.objects.create(name='Other Company')

    def setUp(self):
        self.company = UnitTestCompany.objects.get(pk=1)

    def test_create_user(self):
        UnitTestUser.objects.create_user('a@example.com', 'a', first_name='Joe', last_name='User', company=self.company)
        u = UnitTestUser.objects.get(email='a@example.com')
        assert u
        self.assertEqual(u.first_name, 'Joe')
        self.assertEqual(u.last_name, 'User')
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertTrue(u.is_active)
        self.assertEqual(u.get_full_name(), 'Joe User')
        self.assertEqual(u.get_short_name(), 'Joe')

    def test_create_superuser(self):
        UnitTestUser.objects.create_superuser('a@example.com', 'a', first_name='Joe', last_name='Superuser', company=self.company)
        u = UnitTestUser.objects.get(email='a@example.com')
        assert u
        self.assertEqual(u.first_name, 'Joe')
        self.assertEqual(u.last_name, 'Superuser')
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_superuser)
        self.assertTrue(u.is_active)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
)
class UserTestCase(django.test.TestCase):
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

    def setUp(self):
        self.company = UnitTestCompany.objects.get(pk=1)
        self.superuser = UnitTestUser.objects.get(pk=1)
        self.staff_user = UnitTestUser.objects.get(pk=2)
        self.regular_user = UnitTestUser.objects.get(pk=3)

    def test_get_full_name(self):
        u = UnitTestUser()
        self.assertEqual(u.get_full_name(), '')
        u.email = 'name@example.net'
        self.assertEqual(u.get_full_name(), 'name@example.net')
        u.first_name = 'First'
        self.assertEqual(u.get_full_name(), 'First')
        u.first_name = ''
        u.last_name = 'Last'
        self.assertEqual(u.get_full_name(), 'Last')
        u.first_name = 'First'
        self.assertEqual(u.get_full_name(), 'First Last')

    def test_get_short_name(self):
        u = UnitTestUser()
        self.assertEqual(u.get_short_name(), '')
        u.email = 'name@example.net'
        self.assertEqual(u.get_short_name(), '')
        u.last_name = 'Last'
        self.assertEqual(u.get_short_name(), '')
        u.first_name = 'First'
        self.assertEqual(u.get_short_name(), 'First')

    def test_email_user(self):
        u = UnitTestUser(email='test@example.net')
        u.email_user('Subject', 'Body', 'from@example.net')
        self.assertEqual(1, len(django.core.mail.outbox))
        sent_email = django.core.mail.outbox[0]
        self.assertListEqual(sent_email.to, ['test@example.net'])
        self.assertEqual(sent_email.from_email, 'from@example.net')
        self.assertEqual(sent_email.subject, 'Subject')
        self.assertEqual(sent_email.body, 'Body')
