========
Accounts
========

Account is an app that shall add the following features to your Django project:
1. An inherited User model with extra fields like Company, First Name, Last Name, etc...
2. Masquerading feature.
3. Enabling Timezone to set to the user's local timezone.
4. Audit log model to track extra user specific actions.

Quick start
-----------
1. Add "accounts" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'accounts',
    ]

2. Include the accounts URLconf in your project urls.py like this::

    url(r'^/', include('accounts.urls')),

3. Run `python manage.py migrate` to create the accounts models.

4. Start the development server admin/ to create users and companies. From Users list view, you can take advantage of the masquerading feature.

5. For timezone enablement, add "" to MIDDLEWARE_CLASSES like this::

    MIDDLEWARE_CLASSES = (
        ...
        'accounts.middleware.TimezoneMiddleware',
    )

6. A new Audit Log model added to capture the following events::

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
