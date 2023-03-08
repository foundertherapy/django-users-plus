import django.contrib.auth.signals
from django.dispatch import receiver, Signal
from django.conf import settings
from django.apps import apps


def is_audit_log_enabled():
    return getattr(settings, 'ACCOUNTS_ENABLE_AUDIT_LOG', False)


def is_audit_log_configured():
    return hasattr(settings, 'ACCOUNTS_AUDIT_LOG_EVENT_MODEL')


def log_audit_event(message, **kwargs):
    if is_audit_log_enabled() and is_audit_log_configured():
        user = kwargs['user']
        request = kwargs['request']
        is_masquerading = request.session.get('is_masquerading', False)

        if not user:
            return

        model = apps.get_model(settings.ACCOUNTS_AUDIT_LOG_EVENT_MODEL)

        data = {
            'user_id': user.id,
            'user_email': user.email,
            'message': message,
        }

        if hasattr(user, 'company'):
            company = user.company
            if company:
                data['company_id'] = company.id
                data['company_name'] = company.name

        e = model(**data)

        if is_masquerading:
            masquerading_user = django.contrib.auth.get_user_model().objects.get(pk=request.session['masquerade_user_id'])
            e.masquerading_user_id = masquerading_user.id
            e.masquerading_user_email = masquerading_user.email

        e.save()
        return e


masquerade_start = Signal(providing_args=['request', 'user', 'masquerade_as'])
masquerade_end = Signal(providing_args=['request', 'user'])
user_password_reset_request = Signal(providing_args=['request', 'user'])

user_password_change = Signal(providing_args=['request', 'user'])
user_email_change = Signal(providing_args=['request', 'user', 'old_email', 'new_email'])
user_create = Signal(providing_args=['request', 'user'])
user_deactivate = Signal(providing_args=['request', 'user'])
user_activate = Signal(providing_args=['request', 'user'])

company_name_change = Signal(providing_args=['request', 'company', 'old_name', 'new_name'])


@receiver(django.contrib.auth.signals.user_logged_in)
def login_callback(sender, **kwargs):
    log_audit_event('Sign in', **kwargs)


@receiver(django.contrib.auth.signals.user_logged_out)
def logout_callback(sender, **kwargs):
    log_audit_event('Sign out', **kwargs)


@receiver(masquerade_start)
def masquerade_start_callback(sender, **kwargs):
    masquerade_as = kwargs['masquerade_as']
    message = 'Masquerade start as {} ({})'.format(masquerade_as.email, masquerade_as.id)
    log_audit_event(message, **kwargs)


@receiver(masquerade_end)
def masquerade_end_callback(sender, **kwargs):
    masquerade_as = kwargs['masquerade_as']
    message = 'Masquerade end as {} ({})'.format(masquerade_as.email, masquerade_as.id)
    log_audit_event(message, **kwargs)


@receiver(user_password_reset_request)
def password_reset_request_callback(sender, **kwargs):
    log_audit_event('Request password reset', **kwargs)


@receiver(user_password_change)
def password_change_callback(sender, **kwargs):
    log_audit_event('Change password', **kwargs)


@receiver(user_create)
def create_callback(sender, **kwargs):
    request = kwargs['request']
    message = 'Create by: {} ({})'.format(request.user.email, request.user.id)
    log_audit_event(message, **kwargs)


@receiver(user_email_change)
def email_change_callback(sender, **kwargs):
    old_email = kwargs['old_email']
    new_email = kwargs['new_email']
    message = 'Email change from: {} to: {}'.format(old_email, new_email)
    log_audit_event(message, **kwargs)


@receiver(user_deactivate)
def deactivate_callback(sender, **kwargs):
    request = kwargs['request']
    message = 'Deactivate by: {} ({})'.format(request.user.email, request.user.id)
    log_audit_event(message, **kwargs)


@receiver(user_activate)
def activate_callback(sender, **kwargs):
    request = kwargs['request']
    message = 'Activate by: {} ({})'.format(request.user.email, request.user.id)
    log_audit_event(message, **kwargs)


@receiver(company_name_change)
def company_name_change_callback(sender, **kwargs):
    company = kwargs['company']
    old_name = kwargs['old_name']
    new_name = kwargs['new_name']
    message = 'Company id: {} name change from: {} to: {}'.format(company.id, old_name, new_name)
    log_audit_event(message, **kwargs)
