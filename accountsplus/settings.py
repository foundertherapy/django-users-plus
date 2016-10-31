from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.apps import apps


# Default values
LOCKOUT_TEMPLATE = 'accounts/locked_out.html'

def get_setting(setting_str, is_required, default_value=None):
    try:
        return getattr(settings, setting_str)
    except AttributeError:
        if is_required:
            raise ImproperlyConfigured('Setting {} is not configured in your settings module'.format(setting_str))
        else:
            return default_value


def get_captcha_public_key():
    return get_setting('RECAPTCHA_PUBLIC_KEY', True)


def get_captcha_private_key():
    return get_setting('RECAPTCHA_PRIVATE_KEY', True)


def get_enable_lockout():
    return get_setting('AXES_LOCK_OUT_AT_FAILURE', True)


def get_cooloff_time():
    return get_setting('AXES_COOLOFF_TIME', True)


def get_login_failure_limit():
    return get_setting('AXES_LOGIN_FAILURE_LIMIT', False, 3)


def get_lockout_url():
    return get_setting('AXES_LOCKOUT_URL', False, 'locked/')


def get_lockout_template():
    return get_setting('LOCKOUT_TEMPLATE_PATH', False, LOCKOUT_TEMPLATE)


ENABLE_LOCKOUT = bool(get_enable_lockout())
if ENABLE_LOCKOUT:
    # Check if the required apps are installed
    if not apps.is_installed('axes'):
        raise ImproperlyConfigured('axes is not configured in your INSTALLED_APPS')
    if not apps.is_installed('captcha'):
        raise ImproperlyConfigured('captcha is not configured in your INSTALLED_APPS')

    # Checking if those parameters are configured within the app settings
    PRIVATE_KEY = get_captcha_private_key()
    PUBLIC_KEY = get_captcha_private_key()

    COOLOFF_TIME = int(get_cooloff_time())
    LOGIN_FAILURE_LIMIT = int(get_login_failure_limit())
    LOCKOUT_URL = str(get_lockout_url())
    LOCKOUT_TEMPLATE = get_lockout_template()
