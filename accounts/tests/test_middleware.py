import logging

import django.test
import django.test.client
import django.utils.timezone

from .. import models
from .. import middleware


logging.disable(logging.CRITICAL)


class TimezoneMiddlewareTestCase(django.test.TestCase):
    fixtures = ('test_companies.json', )

    def setUp(self):
        self.factory = django.test.client.RequestFactory()
        self.company = models.Company.objects.get(pk=1)
        self.user = models.User.objects.create_user(
            email='test@example.com', password='top_secret',
            first_name='test', last_name='user', company=self.company)

    def test_process_request(self):
        request = self.factory.get('/admin')
        request.user = self.user
        self.assertEqual(django.utils.timezone.get_current_timezone(), django.utils.timezone.get_default_timezone())
        tz_middleware = middleware.TimezoneMiddleware()
        tz_middleware.process_request(request)
        self.assertEqual(django.utils.timezone.get_current_timezone(), self.user.timezone)
