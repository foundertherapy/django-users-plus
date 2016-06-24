import logging

import django.test
import django.test.client
import django.utils.timezone

from .. import models


logging.disable(logging.CRITICAL)


class ContextProcessorTestCase(django.test.TestCase):
    fixtures = ('test_companies.json', 'test_users.json')

    def setUp(self):
        self.superuser = models.User.objects.get(pk=1)

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
