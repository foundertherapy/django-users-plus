import logging

import django.test
import django.test.client
import django.utils.timezone

import pytz

from .. import middleware
from test_models import (UnitTestCompany, UnitTestUser, )


logging.disable(logging.CRITICAL)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class TimezoneMiddlewareTestCase(django.test.TestCase):
    @classmethod
    def setUpTestData(cls):
        company = UnitTestCompany.objects.create(name='Example')
        UnitTestCompany.objects.create(name='Other Company')
        user = UnitTestUser.objects.create_user(email='test@example.com', password='t', first_name='f', last_name='l')
        user.company = company
        user.save()

    def test_process_request(self):
        factory = django.test.client.RequestFactory()
        user = UnitTestUser.objects.get(pk=1)

        request = factory.get('/admin/')
        request.user = user
        tz_middleware = middleware.TimezoneMiddleware()
        tz_middleware.process_request(request)
        self.assertEqual(django.utils.timezone.get_current_timezone(), user.timezone)

        # test changing user timezone
        user.timezone = pytz.timezone('Asia/Singapore')
        user.save()

        tz_middleware.process_request(request)
        self.assertEqual(django.utils.timezone.get_current_timezone(), user.timezone)
