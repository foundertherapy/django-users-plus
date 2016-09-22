from __future__ import unicode_literals

import logging

from django.utils.translation import ugettext_lazy as _
import django.core.mail
import django.contrib.auth.models
import django.contrib.auth.base_user
import django.db.models
import django.db.models.signals
import django.utils.timezone
import django.core.validators
import django.urls
import django.contrib.sites.models
from django.utils.encoding import python_2_unicode_compatible

import timezone_field
import localflavor.us.models

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class BaseCompany(django.db.models.Model):
    created_on = django.db.models.DateTimeField(auto_now_add=True)
    updated_on = django.db.models.DateTimeField(auto_now=True)

    name = django.db.models.CharField(_('Name'), max_length=100)
    street_address = django.db.models.CharField(_('Street Address'), max_length=200, blank=True)
    street_address_2 = django.db.models.CharField(_('Street Address 2'), max_length=200, blank=True)
    city = django.db.models.CharField(_('City'), max_length=100, blank=True)
    state = localflavor.us.models.USStateField(blank=True)
    postal_code = localflavor.us.models.USZipCodeField(blank=True)

    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')
        abstract = True

    def __str__(self):
        return self.name

    def get_address(self):
        address = [self.name, ]
        if self.street_address:
            address.append(self.street_address)
        if self.street_address_2:
            address.append(self.street_address_2)
        if self.city:
            address.append('{}, {} {}'.format(self.city, self.state, self.postal_code))
        else:
            address.append('{} {}'.format(self.state, self.postal_code))
        return address


class UserManager(django.contrib.auth.base_user.BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not email:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


@python_2_unicode_compatible
class BaseUser(django.contrib.auth.base_user.AbstractBaseUser, django.contrib.auth.models.PermissionsMixin):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', )

    PERMISSION_MASQUERADE = 'accountsplus.masquerade'

    created_on = django.db.models.DateTimeField(auto_now_add=True)
    updated_on = django.db.models.DateTimeField(auto_now=True)

    is_active = django.db.models.BooleanField(_('Active'), default=True)
    is_staff = django.db.models.BooleanField(_('Admin'), default=False)

    first_name = django.db.models.CharField(_('First Name'), max_length=50)
    last_name = django.db.models.CharField(_('Last Name'), max_length=50)
    email = django.db.models.EmailField(_('Email'), unique=True)
    timezone = timezone_field.TimeZoneField(default='America/New_York')

    objects = UserManager()

    class Meta(django.contrib.auth.models.AbstractBaseUser.Meta):
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        permissions = (
            ('masquerade', 'Can sign in as User'),
        )
        abstract = True

    def __init__(self, *args, **kwargs):
        super(BaseUser, self).__init__(*args, **kwargs)
        # hack the admin to change the superuser field verbose name
        superuser_field = self._meta.get_field('is_superuser')
        superuser_field.verbose_name = _('Superuser')

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        return ' '.join([n for n in (self.first_name, self.last_name, ) if n] or [self.email])

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        django.core.mail.send_mail(subject, message, from_email, [self.email], **kwargs)

    def set_random_password(self):
        pw = UserManager().make_random_password()
        self.set_password(pw)
        return pw


@python_2_unicode_compatible
class BaseAuditLogEvent(django.db.models.Model):
    created_on = django.db.models.DateTimeField(auto_now_add=True)
    updated_on = django.db.models.DateTimeField(auto_now=True)
    recorded_on = django.db.models.DateTimeField(auto_now_add=True)

    user_id = django.db.models.IntegerField(_('User ID'), db_index=True)
    user_email = django.db.models.EmailField(_('User Email'), db_index=True)
    company_id = django.db.models.IntegerField(_('Company ID'), db_index=True, blank=True, null=True)
    company_name = django.db.models.CharField(_('Company Name'), max_length=100, db_index=True, blank=True)

    message = django.db.models.TextField(_('Audit Message'))
    masquerading_user_id = django.db.models.IntegerField(_('Masquerading User ID'), db_index=True, blank=True, null=True)
    masquerading_user_email = django.db.models.EmailField(_('Masquerading User Email'), db_index=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        if self.is_masquerading:
            return '{} {} [{}] {}'.format(self.recorded_on, self.user_email, self.masquerading_user_email, self.message)
        else:
            return '{} {} {}'.format(self.recorded_on, self.user_email, self.message)

    def delete(self, using=None, keep_parents=False):
        return

    @property
    def is_masquerading(self):
        return self.masquerading_user_id > 0
