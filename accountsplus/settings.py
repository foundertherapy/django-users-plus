from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.apps import apps
from django.utils.translation import ugettext_lazy as _


# Default values
LOCKOUT_TEMPLATE = 'accounts/locked_out.html'

ENGLISH_LANGUAGE = 'en-us'
SPANISH_LANGUAGE = 'es'
FRENCH_LANGUAGE = 'fr'
PORTUGUESE_LANGUAGE = 'pt'
ARABIC_LANGUAGE = 'ar'
DEFAULT_SUPPORTED_LANGUAGES = (
    (ENGLISH_LANGUAGE, _('English')),
    (SPANISH_LANGUAGE, _('Spanish')),
    (FRENCH_LANGUAGE, _('French')),
    (PORTUGUESE_LANGUAGE, _('Portuguese')),
    (ARABIC_LANGUAGE, _('Arabic')),
)


def get_setting(setting_str, is_required, default_value=None):
    try:
        return getattr(settings, setting_str)
    except AttributeError:
        if is_required:
            raise ImproperlyConfigured('Setting {} is not configured in your settings module'.format(setting_str))
        else:
            return default_value


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

    COOLOFF_TIME = int(get_cooloff_time())
    LOGIN_FAILURE_LIMIT = int(get_login_failure_limit())
    LOCKOUT_URL = str(get_lockout_url())
    LOCKOUT_TEMPLATE = get_lockout_template()


SUPPORTED_LANGUAGES = get_setting('LANGUAGES', False, DEFAULT_SUPPORTED_LANGUAGES)
DEFAULT_LANGUAGE = get_setting('LANGUAGE_CODE', False, ENGLISH_LANGUAGE)
