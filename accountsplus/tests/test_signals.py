import django.test
import django.test.utils

import logging
import mock

import accountsplus.models
import accountsplus.signals

from .. import signals, models
from .test_models import (UnitTestCompany, UnitTestUser, UnitTestAuditLogEvent)

logging.disable(logging.CRITICAL)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class SignalTestCase(django.test.TestCase):
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
        self.session_dict = {
            'is_masquerading': False,
        }

        self.session_dict_masquerade = {
            'is_masquerading': True,
            'masquerade_user_id': 1,
            'masquerade_is_superuser': True,
        }

        def get_item_generator(session_dict):
            def get_item(k, default=None):
                if k in session_dict:
                    return session_dict[k]
                else:
                    return default
            return get_item

        self.user_1 = UnitTestUser.objects.get(pk=1)
        self.user_2 = UnitTestUser.objects.get(pk=2)
        self.user_3 = UnitTestUser.objects.get(pk=3)

        self.company_1 = UnitTestCompany.objects.get(pk=1)
        self.company_2 = UnitTestCompany.objects.get(pk=2)

        # create a mock request
        self.request = mock.MagicMock()
        self.request.session = mock.MagicMock(spec_set=dict)
        self.request.session.__getitem__.side_effect = get_item_generator(self.session_dict)
        self.request.session.get.side_effect = get_item_generator(self.session_dict)
        self.request.user = self.user_1

        # create a mock request for masquerading
        self.request_masquerade = mock.MagicMock()
        self.request_masquerade.session = mock.MagicMock(spec_set=dict)
        self.request_masquerade.session.__getitem__.side_effect = get_item_generator(self.session_dict_masquerade)
        self.request_masquerade.session.get.side_effect = get_item_generator(self.session_dict_masquerade)
        self.request_masquerade.user = self.user_2


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class AuditLogEventHelperCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_is_audit_log_enabled_true(self):
        self.assertTrue(signals.is_audit_log_enabled())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_is_audit_log_enabled_false(self):
        self.assertFalse(signals.is_audit_log_enabled())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_log_audit_event(self):
        signals.log_audit_event(message='Test', request=self.request, user=self.user_1)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 1)
        self.assertEqual(audit_log_event.user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, None)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Test')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_log_audit_event_masquerade(self):
        signals.log_audit_event(message='Test', request=self.request_masquerade, user=self.user_2)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 2)
        self.assertEqual(audit_log_event.user_email, 'staffuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.message, 'Test')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_log_audit_event_no_audit_log(self):
        signals.log_audit_event(message='Test', request=self.request, user=self.user_1)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_log_audit_event_masquerade_no_audit_log(self):
        signals.log_audit_event(message='Test', request=self.request_masquerade, user=self.user_2)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class LoginCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_login_callback(self):
        signals.login_callback(sender=self, request=self.request, user=self.user_1)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 1)
        self.assertEqual(audit_log_event.user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, None)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Sign in')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_login_callback_masquerade(self):
        signals.login_callback(sender=self, request=self.request_masquerade, user=self.user_2)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 2)
        self.assertEqual(audit_log_event.user_email, 'staffuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.message, 'Sign in')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_login_callback_no_audit_log(self):
        signals.login_callback(sender=self, request=self.request, user=self.user_1)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_login_callback_masquerade_no_audit_log(self):
        signals.login_callback(sender=self, request=self.request_masquerade, user=self.user_2)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        import django.contrib.auth.signals
        receivers = django.contrib.auth.signals.user_logged_in._live_receivers(self)
        self.assertIn(signals.login_callback, receivers)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class LogoutCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_logout_callback(self):
        signals.logout_callback(sender=self, request=self.request, user=self.user_1)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 1)
        self.assertEqual(audit_log_event.user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, None)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Sign out')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_logout_callback_masquerade(self):
        signals.logout_callback(sender=self, request=self.request_masquerade, user=self.user_2)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 2)
        self.assertEqual(audit_log_event.user_email, 'staffuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.message, 'Sign out')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_logout_callback_no_audit_log(self):
        signals.logout_callback(sender=self, request=self.request, user=self.user_1)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_logout_callback_masquerade_no_audit_log(self):
        signals.logout_callback(sender=self, request=self.request_masquerade, user=self.user_2)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        import django.contrib.auth.signals
        receivers = django.contrib.auth.signals.user_logged_out._live_receivers(self)
        self.assertIn(signals.logout_callback, receivers)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class MasqueradeStartCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_masquerade_start_callback(self):
        signals.masquerade_start_callback(sender=self, request=self.request, user=self.user_1, masquerade_as=self.user_2)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 1)
        self.assertEqual(audit_log_event.user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertIsNone(audit_log_event.masquerading_user_id)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Masquerade start as staffuser@example.com (2)')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_masquerade_start_callback_no_audit_log(self):
        signals.masquerade_start_callback(sender=self, request=self.request, user=self.user_1, masquerade_as=self.user_2)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        receivers = accountsplus.signals.masquerade_start._live_receivers(self)
        self.assertIn(signals.masquerade_start_callback, receivers)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class MasqueradeEndCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_masquerade_end_callback(self):
        signals.masquerade_end_callback(sender=self, request=self.request, user=self.user_1, masquerade_as=self.user_2)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 1)
        self.assertEqual(audit_log_event.user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertIsNone(audit_log_event.masquerading_user_id)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Masquerade end as staffuser@example.com (2)')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_masquerade_end_callback_no_audit_log(self):
        signals.masquerade_end_callback(sender=self, request=self.request, user=self.user_1, masquerade_as=self.user_2)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        receivers = accountsplus.signals.masquerade_end._live_receivers(self)
        self.assertIn(signals.masquerade_end_callback, receivers)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class PasswordResetCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_password_reset_callback(self):
        signals.password_reset_request_callback(sender=self, request=self.request, user=self.user_1)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 1)
        self.assertEqual(audit_log_event.user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, None)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Request password reset')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_password_reset_callback_masquerade(self):
        signals.password_reset_request_callback(sender=self, request=self.request_masquerade, user=self.user_2)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 2)
        self.assertEqual(audit_log_event.user_email, 'staffuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.message, 'Request password reset')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_password_reset_callback_no_audit_log(self):
        signals.password_reset_request_callback(sender=self, request=self.request, user=self.user_1)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_password_reset_callback_masquerade_no_audit_log(self):
        signals.password_reset_request_callback(sender=self, request=self.request_masquerade, user=self.user_2)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        receivers = accountsplus.signals.user_password_reset_request._live_receivers(self)
        self.assertIn(signals.password_reset_request_callback, receivers)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class PasswordChangeCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_password_change_callback(self):
        signals.password_change_callback(sender=self, request=self.request, user=self.user_1)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 1)
        self.assertEqual(audit_log_event.user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, None)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Change password')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_password_change_callback_masquerade(self):
        signals.password_change_callback(sender=self, request=self.request_masquerade, user=self.user_2)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 2)
        self.assertEqual(audit_log_event.user_email, 'staffuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.message, 'Change password')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_password_change_callback_no_audit_log(self):
        signals.password_change_callback(sender=self, request=self.request, user=self.user_1)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_password_change_callback_masquerade_no_audit_log(self):
        signals.password_change_callback(sender=self, request=self.request_masquerade, user=self.user_2)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        receivers = accountsplus.signals.user_password_change._live_receivers(self)
        self.assertIn(signals.password_change_callback, receivers)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class CreateCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_create_callback(self):
        signals.create_callback(sender=self, request=self.request, user=self.user_3)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 3)
        self.assertEqual(audit_log_event.user_email, 'regularuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, None)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Create by: superuser@example.com (1)')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_create_callback_masquerade(self):
        signals.create_callback(sender=self, request=self.request_masquerade, user=self.user_3)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 3)
        self.assertEqual(audit_log_event.user_email, 'regularuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.message, 'Create by: staffuser@example.com (2)')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_create_callback_no_audit_log(self):
        signals.create_callback(sender=self, request=self.request, user=self.user_3)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_create_callback_masquerade_no_audit_log(self):
        signals.create_callback(sender=self, request=self.request_masquerade, user=self.user_3)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        receivers = accountsplus.signals.user_create._live_receivers(self)
        self.assertIn(signals.create_callback, receivers)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class EmailChangeCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_email_change_callback(self):
        signals.email_change_callback(
            sender=self, request=self.request, user=self.user_3, old_email='regularuser@example.com',
            new_email='change@example.com')
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 3)
        self.assertEqual(audit_log_event.user_email, 'regularuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, None)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Email change from: regularuser@example.com to: change@example.com')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_email_change_callback_masquerade(self):
        signals.email_change_callback(
            sender=self, request=self.request_masquerade, user=self.user_3, old_email='regularuser@example.com',
            new_email='change@example.com')
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 3)
        self.assertEqual(audit_log_event.user_email, 'regularuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.message, 'Email change from: regularuser@example.com to: change@example.com')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_email_change_callback_no_audit_log(self):
        signals.email_change_callback(
            sender=self, request=self.request, user=self.user_3, old_email='regularuser@example.com',
            new_email='change@example.com')
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_email_change_callback_masquerade_no_audit_log(self):
        signals.email_change_callback(
            sender=self, request=self.request_masquerade, user=self.user_3, old_email='regularuser@example.com',
            new_email='change@example.com')
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        receivers = accountsplus.signals.user_email_change._live_receivers(self)
        self.assertIn(signals.email_change_callback, receivers)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class DeactivateCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_deactivate_callback(self):
        signals.deactivate_callback(sender=self, request=self.request, user=self.user_3)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 3)
        self.assertEqual(audit_log_event.user_email, 'regularuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, None)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Deactivate by: superuser@example.com (1)')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_deactivate_callback_masquerade(self):
        signals.deactivate_callback(sender=self, request=self.request_masquerade, user=self.user_3)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 3)
        self.assertEqual(audit_log_event.user_email, 'regularuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.message, 'Deactivate by: staffuser@example.com (2)')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_deactivate_callback_no_audit_log(self):
        signals.deactivate_callback(sender=self, request=self.request, user=self.user_3)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_deactivate_callback_masquerade_no_audit_log(self):
        signals.deactivate_callback(sender=self, request=self.request_masquerade, user=self.user_3)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        receivers = accountsplus.signals.user_deactivate._live_receivers(self)
        self.assertIn(signals.deactivate_callback, receivers)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class ActivateCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_activate_callback(self):
        signals.activate_callback(sender=self, request=self.request, user=self.user_3)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 3)
        self.assertEqual(audit_log_event.user_email, 'regularuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, None)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Activate by: superuser@example.com (1)')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_activate_callback_masquerade(self):
        signals.activate_callback(sender=self, request=self.request_masquerade, user=self.user_3)
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 3)
        self.assertEqual(audit_log_event.user_email, 'regularuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.message, 'Activate by: staffuser@example.com (2)')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_activate_callback_no_audit_log(self):
        signals.activate_callback(sender=self, request=self.request, user=self.user_3)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_activate_callback_masquerade_no_audit_log(self):
        signals.activate_callback(sender=self, request=self.request_masquerade, user=self.user_3)
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        receivers = accountsplus.signals.user_activate._live_receivers(self)
        self.assertIn(signals.activate_callback, receivers)


@django.test.utils.override_settings(
    AUTH_USER_MODEL='accountsplus.UnitTestUser',
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL='accountsplus.UnitTestAuditLogEvent',
)
class CompanyNameChangeCallbackTestCase(SignalTestCase):
    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_company_name_change_callback(self):
        signals.company_name_change_callback(
            sender=self, request=self.request, user=self.user_3, company=self.company_2, old_name='Old Name', new_name='New Name')
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 3)
        self.assertEqual(audit_log_event.user_email, 'regularuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, None)
        self.assertEqual(audit_log_event.masquerading_user_email, '')
        self.assertEqual(audit_log_event.message, 'Company id: 2 name change from: Old Name to: New Name')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=True)
    def test_company_name_change_callback_masquerade(self):
        signals.company_name_change_callback(
            sender=self, request=self.request_masquerade, user=self.user_3, company=self.company_2, old_name='Old Name',
            new_name='New Name')
        audit_log_event = UnitTestAuditLogEvent.objects.get()
        self.assertEqual(audit_log_event.user_id, 3)
        self.assertEqual(audit_log_event.user_email, 'regularuser@example.com')
        self.assertEqual(audit_log_event.company_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_id, 1)
        self.assertEqual(audit_log_event.masquerading_user_email, 'superuser@example.com')
        self.assertEqual(audit_log_event.message, 'Company id: 2 name change from: Old Name to: New Name')

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_company_name_change_callback_no_audit_log(self):
        signals.company_name_change_callback(
            sender=self, request=self.request, user=self.user_3, company=self.company_2, old_name='Old Name', new_name='New Name')
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    @django.test.utils.override_settings(ACCOUNTS_ENABLE_AUDIT_LOG=False)
    def test_company_name_change_callback_masquerade_no_audit_log(self):
        signals.company_name_change_callback(
            sender=self, request=self.request_masquerade, user=self.user_3, company=self.company_2, old_name='Old Name',
            new_name='New Name')
        self.assertEqual(0, UnitTestAuditLogEvent.objects.count())

    def test_signal_registration(self):
        receivers = accountsplus.signals.company_name_change._live_receivers(self)
        self.assertIn(signals.company_name_change_callback, receivers)

