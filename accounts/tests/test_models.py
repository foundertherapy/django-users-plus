from __future__ import unicode_literals

import django.test
import django.core.mail

import logging

from .. import models


logging.disable(logging.CRITICAL)


class UserManagerTestCase(django.test.TestCase):
    fixtures = ('test_companies.json', )

    def setUp(self):
        self.company = models.Company.objects.get(pk=1)

    def test_create_user(self):
        models.User.objects.create_user('a@example.com', 'a', 'Joe', 'User', company=self.company)
        u = models.User.objects.get(email='a@example.com')
        assert u
        self.assertEqual(u.first_name, 'Joe')
        self.assertEqual(u.last_name, 'User')
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertTrue(u.is_active)
        self.assertEqual(u.get_full_name(), 'Joe User')
        self.assertEqual(u.get_short_name(), 'Joe')

    def test_create_superuser(self):
        models.User.objects.create_superuser('a@example.com', 'a', 'Joe', 'Superuser', company=self.company)
        u = models.User.objects.get(email='a@example.com')
        assert u
        self.assertEqual(u.first_name, 'Joe')
        self.assertEqual(u.last_name, 'Superuser')
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_superuser)
        self.assertTrue(u.is_active)


class UserTestCase(django.test.TestCase):
    fixtures = ('test_companies.json', 'test_users.json', )

    def setUp(self):
        self.company = models.Company.objects.get(pk=1)
        self.superuser = models.User.objects.get(pk=1)
        self.staff_user = models.User.objects.get(pk=2)
        self.regular_user = models.User.objects.get(pk=3)

    def test_get_full_name(self):
        u = models.User()
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
        u = models.User()
        self.assertEqual(u.get_short_name(), '')
        u.email = 'name@example.net'
        self.assertEqual(u.get_short_name(), '')
        u.last_name = 'Last'
        self.assertEqual(u.get_short_name(), '')
        u.first_name = 'First'
        self.assertEqual(u.get_short_name(), 'First')

    def test_email_user(self):
        u = models.User(email='test@example.net')
        u.email_user('Subject', 'Body', 'from@example.net')
        self.assertEqual(1, len(django.core.mail.outbox))
        sent_email = django.core.mail.outbox[0]
        self.assertListEqual(sent_email.to, ['test@example.net'])
        self.assertEqual(sent_email.from_email, 'from@example.net')
        self.assertEqual(sent_email.subject, 'Subject')
        self.assertEqual(sent_email.body, 'Body')
