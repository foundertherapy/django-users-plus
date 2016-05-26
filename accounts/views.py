from __future__ import unicode_literals
import logging
from django.utils.translation import ugettext as _
import django.views.decorators.cache
import django.views.decorators.csrf
import django.views.decorators.debug
import django.contrib.auth.decorators
import django.contrib.auth.views
import django.contrib.auth.forms
import django.contrib.auth
import django.contrib.messages
import django.shortcuts
import django.http
import django.template.response
import django.utils.module_loading

import django.core.urlresolvers

import models
import signals

logger = logging.getLogger(__name__)


from django.views.generic.edit import FormView


def logout_then_login(
        request, login_url=None, current_app=None, extra_context=None):
    """
    Logs out the user if they are logged in. Then redirects to the log-in page.
    """
    # if a user is masquerading, don't log them out, just kill the masquerade
    if request.session.get('is_masquerading'):
        return django.shortcuts.redirect('end_masquerade')
    else:
        return django.contrib.auth.views.logout_then_login(
            request, login_url, current_app, extra_context)


@django.views.decorators.cache.never_cache
@django.contrib.auth.decorators.login_required
def masquerade(request, user_id=None):
    return_page = request.META.get('HTTP_REFERER') or \
        'admin:accounts_user_changelist'
    if not user_id:
        django.contrib.messages.error(
            request, 'Masquerade failed: no user specified')
        return django.shortcuts.redirect(return_page)
    if not request.user.has_perm(models.User.PERMISSION_MASQUERADE):
        django.contrib.messages.error(
            request, 'Masquerade failed: insufficient privileges')
        return django.shortcuts.redirect(return_page)

    try:
        user = models.User.objects.get(pk=user_id)
    except models.User.DoesNotExist:
        logger.error('User {} ({}) masquerading failed for user {}'.format(
            request.user.email, request.user.id, user_id))
        django.contrib.messages.error(
            request, 'Masquerade failed: unknown user {}'.format(user_id))
        return django.shortcuts.redirect(return_page)

    if user.is_superuser:
        logger.warning(
            'User {} ({}) cannot masquerade as superuser {} ({})'.format(
                request.user.email, request.user.id, user.email, user.id))
        django.contrib.messages.warning(
            request, 'Cannot masquerade as a superuser')
        return django.shortcuts.redirect(return_page)

    admin_user = request.user
    user.backend = request.session[django.contrib.auth.BACKEND_SESSION_KEY]
    # log the new user in
    signals.masquerade_start.send(
        sender=masquerade, request=request, user=admin_user, masquerade_as=user)
    # this is needed to track whether this login is for a masquerade
    setattr(user, 'is_masquerading', True)
    setattr(user, 'masquerading_user', admin_user)
    django.contrib.auth.login(request, user)

    request.session['is_masquerading'] = True
    request.session['masquerade_user_id'] = admin_user.id
    request.session['return_page'] = return_page
    request.session['masquerade_is_superuser'] = admin_user.is_superuser

    logger.info(
        'User {} ({}) masquerading as {} ({})'.format(
            admin_user.email, admin_user.id,
            request.user.email, request.user.id))
    django.contrib.messages.success(
        request, 'Masquerading as user {0}'.format(user.email))

    return django.shortcuts.redirect('admin:index')


@django.views.decorators.cache.never_cache
@django.contrib.auth.decorators.login_required
def end_masquerade(request):
    if 'is_masquerading' not in request.session:
        return django.shortcuts.redirect('admin:index')

    if 'masquerade_user_id' in request.session:
        try:
            masqueraded_user = request.user
            user = models.User.objects.get(
                pk=request.session['masquerade_user_id'])
            user.backend = request.session[
                django.contrib.auth.BACKEND_SESSION_KEY]
            # this is needed to track whether this login is for a masquerade
            django.contrib.auth.logout(request)
            signals.masquerade_end.send(
                sender=end_masquerade, request=request, user=user,
                masquerade_as=masqueraded_user)
            django.contrib.auth.login(request, user)
            logging.info('End masquerade user: {} ({}) by: {} ({})'.format(
                masqueraded_user.email, masqueraded_user.id,
                user.email, user.id))
            django.contrib.messages.success(request, 'Masquerade ended')
        except models.User.DoesNotExist as e:
            logging.critical(
                'Masquerading user {} does not exist'.format(
                    request.session['masquerade_user_id']))

    return django.shortcuts.redirect('admin:accounts_user_changelist')


@django.views.decorators.debug.sensitive_post_parameters()
@django.views.decorators.csrf.csrf_protect
@django.contrib.auth.decorators.login_required
def password_change(request,
                    template_name='registration/password_change_form.html',
                    post_change_redirect=None,
                    password_change_form=django.contrib.auth.forms.
                    PasswordChangeForm,
                    current_app=None, extra_context=None):
    if post_change_redirect is None:
        post_change_redirect = django.core.urlresolvers.reverse(
            'password_change_done')
    else:
        post_change_redirect = django.shortcuts.resolve_url(
            post_change_redirect)
    if request.method == "POST":
        form = password_change_form(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Updating the password logs out all other sessions for the user
            # except the current one if
            # django.contrib.auth.middleware.SessionAuthenticationMiddleware
            # is enabled.
            django.contrib.auth.update_session_auth_hash(request, form.user)
            signals.user_password_change.send(
                sender=password_change, request=request, user=form.user)
            return django.http.HttpResponseRedirect(post_change_redirect)
    else:
        form = password_change_form(user=request.user)
    context = {
        'form': form,
        'title': _('Password change'),
    }
    if extra_context is not None:
        context.update(extra_context)
    return django.template.response.TemplateResponse(
        request, template_name, context, current_app=current_app)


@django.views.decorators.csrf.csrf_protect
def password_reset(request, is_admin_site=False,
                   template_name='registration/password_reset_form.html',
                   email_template_name='registration/password_reset_email.html',
                   subject_template_name='registration/password_reset_subject.txt',
                   password_reset_form=django.contrib.auth.forms.PasswordResetForm,
                   token_generator=django.contrib.auth.views.default_token_generator,
                   post_reset_redirect=None,
                   from_email=None,
                   current_app=None,
                   extra_context=None,
                   html_email_template_name=None):
    response = django.contrib.auth.views.password_reset(
        request, is_admin_site, template_name, email_template_name,
        subject_template_name, password_reset_form, token_generator,
        post_reset_redirect, from_email, current_app, extra_context,
        html_email_template_name)
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = models.User.objects.get(email=email)
            signals.user_password_reset_request.send(
                sender=password_reset, request=request, user=user)
        except models.User.DoesNotExist:
            pass
    return response
