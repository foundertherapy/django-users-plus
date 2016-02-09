========
Accounts
========

Account is an app that shall add the following features to your Django project:
1. An inherited User model with extra fields like Company, Address, etc...
2. Masquerading feature.
3. Enabling Timezone to set to the user's local timezone.

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

4. Start the development server and visit http://127.0.0.1:8000/admin/ to create users and companies, from Users list view
you can take advantage of the masquerading feature.
