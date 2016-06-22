.. image:: https://circleci.com/gh/foundertherapy/django-users-plus.svg?style=svg
    :target: https://circleci.com/gh/foundertherapy/django-users-plus

========
Accounts
========

Account is an app that shall add the following features to your Django project::

1. An inherited User model with extra fields like Company, First Name, Last Name, etc...

2. Create users and login using email address instead of username.

3. Masquerading feature.

4. Enabling Timezone to set to the user's local timezone.

5. Audit log model to track extra user specific actions.

Quick start
-----------
1. Add "accounts" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'accounts',
        'django.contrib.sites',
    ]


2. This library will use the default AuditLogEvent model for events logging, if you need to customize it, please extend it in your app, and add the following tho the settings::

```
AUDIT_LOG_EVENT_MODEL = '<app name>.<the name of the model that is extending the base AuditLogEvent>'
```

3.Include the accounts URLconf in your project urls.py like this::

    url(r'^', include('accounts.urls')),

4.  Add SITE_ID into settings file.

5. Run `python manage.py migrate` to create the accounts models.

6. Start the development server admin/ to create users and companies. From Users list view, you can take advantage of the masquerading feature.

7. For timezone enablement, add "" to MIDDLEWARE_CLASSES like this::

    MIDDLEWARE_CLASSES = (
        ...
        'accounts.middleware.TimezoneMiddleware',
    )

8. A new Audit Log model added to capture the following events::

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
