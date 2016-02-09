from __future__ import unicode_literals
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
APPSERVER = os.uname()[1]

# Parse database configuration from $DATABASE_URL
import dj_database_url
DATABASE_URL = os.environ.get(u'DATABASE_URL', u'sqlite:///accounts.sqlite')
DATABASES = {
    u'default': dj_database_url.parse(DATABASE_URL),
}

ROOT_URLCONF = 'urls'

SITE_ID = 1
INTERNAL_IPS = ('127.0.0.1', )
ALLOWED_HOSTS = ['localhost', '127.0.0.1', ]
APPEND_SLASH = True
TIME_ZONE = 'UTC'
USE_TZ = True
SECRET_KEY = 'abc'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sessions',
    'localflavor',
    'accounts',
)

AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = 'index'

MIDDLEWARE_CLASSES = (
    'djangosecure.middleware.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'accounts.middleware.TimezoneMiddleware',
)

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_REDIS_PREFIX = 'session:53'
SESSION_COOKIE_AGE = 60 * 30  # 30 minute session length

# STATICFILES_FINDERS = (
#     'django.contrib.staticfiles.finders.FileSystemFinder',
#     'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#     'pipeline.finders.CachedFileFinder',
#     'pipeline.finders.PipelineFinder',
# )
#
# PASSWORD_HASHERS = (
#     'django.contrib.auth.hashers.BCryptPasswordHasher',
#     'django.contrib.auth.hashers.PBKDF2PasswordHasher',
#     'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
#     'django.contrib.auth.hashers.SHA1PasswordHasher',
#     'django.contrib.auth.hashers.MD5PasswordHasher',
#     'django.contrib.auth.hashers.CryptPasswordHasher',
# )
#
# DATETIME_INPUT_FORMATS = (
#     '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S',
#     '%m/%d/%Y %H:%M', '%m/%d/%Y', '%m/%d/%Y %H:%M:%S',
#     '%m/%d/%y %H:%M', '%m/%d/%y', '%m/%d/%y %H:%M:%S',
# )
#
# MIDDLEWARE_CLASSES = (
#     # 'sslify.middleware.SSLifyMiddleware',
#     'djangosecure.middleware.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'corsheaders.middleware.CorsMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
#     'waffle.middleware.WaffleMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
#     'accounts.middleware.TimezoneMiddleware',
# )
#
#
# TEMPLATE_CONTEXT_PROCESSORS = (
#     'django.contrib.auth.context_processors.auth',
#     'django.core.context_processors.debug',
#     'django.core.context_processors.media',
#     'django.core.context_processors.static',
#     'django.contrib.messages.context_processors.messages',
#     'django.core.context_processors.request',
# )
#
# TEMPLATE_DIRS = (
#     os.path.join(BASE_DIR, 'templates'),
# )
