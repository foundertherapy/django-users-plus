from __future__ import unicode_literals

import logging

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import django.core.mail
import django.contrib.auth.models
import django.db.models
import django.db.models.signals
import django.utils.timezone
import django.core.validators
import django.core.urlresolvers
import django.contrib.sites.models
from django.conf import settings
from django.apps import apps

import timezone_field
import localflavor.us.models

logger = logging.getLogger(__name__)


class Company(django.db.models.Model):
    created_on = django.db.models.DateTimeField(auto_now_add=True)
    updated_on = django.db.models.DateTimeField(auto_now=True)

    name = django.db.models.CharField(_('Name'), max_length=100)
    street_address = django.db.models.CharField(_('Street Address'), max_length=200, blank=True)
    street_address_2 = django.db.models.CharField(_('Street Address 2'), max_length=200, blank=True)
    city = django.db.models.CharField(_('City'), max_length=100, blank=True)
    state = localflavor.us.models.USStateField(blank=True)
    postal_code = localflavor.us.models.USZipCodeField(blank=True)

    class Meta(django.contrib.auth.models.AbstractBaseUser.Meta):
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')

    def __unicode__(self):
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


class UserManager(django.contrib.auth.models.BaseUserManager):
    def create_user(self, email, password, first_name, last_name, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        email = UserManager.normalize_email(email)
        user = apps.get_model(settings.AUTH_USER_MODEL)(
            email=email, first_name=first_name, last_name=last_name,
            is_staff=False, is_active=True, is_superuser=False, **extra_fields)
        user.set_password(password)
        user.last_login = timezone.now()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, first_name, last_name, **extra_fields):
        u = self.create_user(email, password, first_name, last_name, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


class AbstractUser(django.contrib.auth.models.AbstractBaseUser, django.contrib.auth.models.PermissionsMixin):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', )

    PERMISSION_MASQUERADE = 'accounts.masquerade'

    created_on = django.db.models.DateTimeField(auto_now_add=True)
    updated_on = django.db.models.DateTimeField(auto_now=True)

    is_active = django.db.models.BooleanField(_('Active'), default=True)
    is_staff = django.db.models.BooleanField(_('Staff'), default=False)

    first_name = django.db.models.CharField(_('First Name'), max_length=50)
    last_name = django.db.models.CharField(_('Last Name'), max_length=50)
    email = django.db.models.EmailField(_('Email'), unique=True)
    timezone = timezone_field.TimeZoneField(default='America/New_York')

    company = django.db.models.ForeignKey(Company, null=True, related_name='%(app_label)s_%(class)s_users')

    objects = UserManager()

    class Meta(django.contrib.auth.models.AbstractBaseUser.Meta):
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        permissions = (
            ('masquerade', 'Can Masquerade'),
        )
        abstract = True
        swappable = 'AUTH_USER_MODEL'

    def __init__(self, *args, **kwargs):
        super(AbstractUser, self).__init__(*args, **kwargs)
        # hack the admin to change the superuser field verbose name
        superuser_field = self._meta.get_field('is_superuser')
        superuser_field.verbose_name = _('Superuser')

    def __unicode__(self):
        return self.get_full_name()

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        names = [n for n in (self.first_name, self.last_name, ) if n]
        if names:
            return ' '.join(names)
        else:
            return self.email

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


class User(AbstractUser):
    pass


class AbstractAuditLogEventBase(django.db.models.Model):
    created_on = django.db.models.DateTimeField(auto_now_add=True)
    updated_on = django.db.models.DateTimeField(auto_now=True)
    recorded_on = django.db.models.DateTimeField(auto_now_add=True)

    user_id = django.db.models.IntegerField(_('User ID'), db_index=True)
    user_email = django.db.models.EmailField(_('User Email'), db_index=True)
    company = django.db.models.ForeignKey('accounts.Company', null=True, on_delete=django.db.models.SET_NULL,
                                          related_name='%(app_label)s_%(class)s_users')

    message = django.db.models.TextField(_('Audit Message'))
    masquerading_user_id = django.db.models.IntegerField(_('Masquerading User ID'), db_index=True, blank=True, null=True)
    masquerading_user_email = django.db.models.EmailField(_('Masquerading User Email'), db_index=True, blank=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        if self.is_masquerading:
            return '{} {} [{}] {}'.format(self.recorded_on, self.user_email, self.masquerading_user_email, self.message)
        else:
            return '{} {} {}'.format(self.recorded_on, self.user_email, self.message)

    def delete(self, using=None):
        return

    @property
    def is_masquerading(self):
        return self.masquerading_user_id > 0


class AuditLogEvent(AbstractAuditLogEventBase):
    pass
