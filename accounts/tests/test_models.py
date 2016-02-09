from __future__ import unicode_literals

import django.test

import logging
import datetime

from .. import models


logging.disable(logging.CRITICAL)


class UserManagerTestCase(django.test.TestCase):
    fixtures = ('test_companies.json', )

    def setUp(self):
        self.company = models.Company.objects.get(pk=1)

    def test_create_user(self):
        models.User.objects.create_user(
            'a@example.com', 'a', 'Joe', 'User', company=self.company)
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
        models.User.objects.create_superuser(
            'a@example.com', 'a', 'Joe', 'Superuser', company=self.company)
        u = models.User.objects.get(email='a@example.com')
        assert u
        self.assertEqual(u.first_name, 'Joe')
        self.assertEqual(u.last_name, 'Superuser')
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_superuser)
        self.assertTrue(u.is_active)


class FakeDatetime(datetime.datetime):
    pass
