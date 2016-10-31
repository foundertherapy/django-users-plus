.. image:: https://circleci.com/gh/foundertherapy/django-users-plus.svg?style=svg
    :target: https://circleci.com/gh/foundertherapy/django-users-plus

========
AccountsPlus
========

accountsplus is an app that adds the following features to your Django project::

1. An swappable User model that uses email as the username for sign in, and has a timezone field (and supporting middleware) that will show localized times in the Admin site.

2. The ability to sign-in as another User from the User admin screen. This is enabled for superusers, any User that has masquerading permissions. By default, staff users cannot sign-in as other users, and they can never sign in as a superuser (bypassing permission checks) even with masquerading permission.

3. A configurable audit log model that can track a number of admin activities automatically, and can be extended to track additional ones through direct use or through signals. The audit log automatically tracks the user signed into the admin, and if a user is masquerading as another user, that's noted as well.

    - User creation
    - User login
    - User logout
    - User email change
    - Masquerade start
    - Masquerade end
    - Password change
    - Password reset
    - Activate user
    - Deactivate user
    - Company name change


Quick start
-----------
1. Add "accountsplus" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'accountsplus',
        'django.contrib.sites',
        'captcha',
        'timezone_field',
        'axes',
    ]

2. Create your own models for Company, User, and AuditLogEvent, and related Admin classes that inherit from the base models provided in this library. You cannot use the models as provided because they are all declared abstract. This allows you to easily implement a relationship between User and Company that (at the moment) is very difficult to have built into the provided abstract base models. For example::

    class MyCompany(models.BaseCompany):
        bar = django.db.models.CharField(max_length=100)


    class MyUser(models.BaseUser):
        foo = django.db.models.CharField(max_length=100)
        company = django.db.models.ForeignKey('MyCompany', null=True, related_name='users')


    class MyAuditLogEvent(models.BaseAuditLogEvent):
        baz = django.db.models.CharField(max_length=100)

3. Configure the swappable User model in settings::

    AUTH_USER_MODEL = '<app_name>.<your User-inherited model>'

4. Configure the swappable AuditLogEvent model for event logging. This is optional, but without it the AuditLogEvent signals will not work::

    ACCOUNTS_ENABLE_AUDIT_LOG = True
    ACCOUNTS_AUDIT_LOG_EVENT_MODEL = '<app name>.<your AuditLogEvent-inherited model>'

5. Include the accountsplus URLconf in your project urls.py like this::

    url(r'^', include('accountsplus.urls')),

6. To enable timezone support for users in the Admin site, add the following to MIDDLEWARE::

    MIDDLEWARE = (
        ...
        'accountsplus.middleware.TimezoneMiddleware',
    )

7. As a security enhancement, you could enable blocking users from login after a specified number of failing login trials::
    1. To enable locking out through setting the following in your base.py::
        1. In your requirements.txt, add the following line (This is temporary until django-axes fix an issue with IP Tracking)::

            git+https://github.com/foundertherapy/django-axes.git@remove_dependency_on_ip

        2. Required Fields::

            RECAPTCHA_PUBLIC_KEY = <Key generated from Google Recaptcha API>
            RECAPTCHA_PRIVATE_KEY = <Key generated from Google Recaptcha API>
            AXES_LOCK_OUT_AT_FAILURE = True
            AXES_COOLOFF_TIME = <Integer number of hours to block user>

        3. Optional Configurations::

            AXES_LOGIN_FAILURE_LIMIT = Count of failing attempts before lockout. Default 3
            AXES_LOCKOUT_URL = URL pattern for the html template of unlocking blocked users. Default 'locked/'
            LOCKOUT_TEMPLATE_PATH = Template you want to show on lockout. Default 'accounts/locked_out.html'

        4. If you override AXES_LOCKOUT_URL, you need to add some url mappings in your urls.py::

            url(r'^login/<URL_PATTERN>$', accountsplus.views.UserLockedOutView.as_view(), name='locked_out')
            url(r'^admin/login/<URL_PATTERN>$', accountsplus.views.AdminLockedOutView.as_view(), name='locked_out'),

    2. To disable locking out just use, no other configuration is needed::

        AXES_LOCK_OUT_AT_FAILURE = False

    3. For more information on those libraries, check the following docs::
        1. [django-axes](https://django-axes.readthedocs.io/en/latest/)
        2. [django-recaptcha](https://github.com/praekelt/django-recaptcha)
