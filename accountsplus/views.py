import logging

from django.utils.translation import ugettext as _
import django.views.decorators.cache
import django.views.decorators.csrf
import django.views.decorators.debug
import django.views.generic
import django.contrib.auth.decorators
import django.contrib.auth.views
import django.contrib.auth.forms
import django.contrib.auth
import django.contrib.messages
import django.shortcuts
import django.http
import django.template.response
import django.utils.module_loading
import django.urls
from django.conf import settings as app_settings
from django.apps import apps

from axes import utils

from accountsplus import signals
from accountsplus import forms
from accountsplus import settings as accounts_settings


logger = logging.getLogger(__name__)

SESSION_IS_MASQUERADING = 'is_masquerading'
SESSION_MASQUERADE_USER_ID = 'masquerade_user_id'


def logout_then_login(request, login_url=None):
    """
    Logs out the user if they are logged in. Then redirects to the log-in page.
    """
    # if a user is masquerading, don't log them out, just kill the masquerade
    if request.session.get('is_masquerading'):
        return django.shortcuts.redirect('end_masquerade')
    else:
        return django.contrib.auth.views.logout_then_login(request, login_url)


class MasqueradeUserView(django.views.generic.RedirectView):

    def get(self, request, *args, **kwargs):
        admin_user = request.user

        if not request.user.is_superuser:
            django.contrib.messages.error(request, 'Masquerade failed: superuser only can masquerade')
            return super(MasqueradeUserView, self).get(request, *args, **kwargs)

        User = apps.get_model(app_settings.AUTH_USER_MODEL)
        user = User.objects.get(pk=kwargs['user_id'])
        user.backend = request.session[django.contrib.auth.BACKEND_SESSION_KEY]
        django.contrib.auth.login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        request.session[SESSION_IS_MASQUERADING] = True
        request.session[SESSION_MASQUERADE_USER_ID] = admin_user.id
        return super(MasqueradeUserView, self).get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return accounts_settings.LOGIN_REDIRECT_URL


class EndMasqueradeUserView(django.views.generic.RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return django.urls.reverse_lazy('admin:index')

    def get(self, request, *args, **kwargs):
        User = apps.get_model(app_settings.AUTH_USER_MODEL)
        user = User.objects.get(pk=request.session[SESSION_MASQUERADE_USER_ID])
        user.backend = request.session[django.contrib.auth.BACKEND_SESSION_KEY]
        django.contrib.auth.logout(request)
        django.contrib.auth.login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return super(EndMasqueradeUserView, self).get(request, *args, **kwargs)


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
        post_change_redirect = django.urls.reverse(
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
    return django.template.response.TemplateResponse(request, template_name, context)


@django.views.decorators.csrf.csrf_protect
def password_reset(request,
                   template_name='registration/password_reset_form.html',
                   email_template_name='registration/password_reset_email.html',
                   subject_template_name='registration/password_reset_subject.txt',
                   password_reset_form=django.contrib.auth.forms.PasswordResetForm,
                   token_generator=django.contrib.auth.views.default_token_generator,
                   post_reset_redirect=None,
                   from_email=None,
                   current_app=None,
                   extra_context=None,
                   html_email_template_name=None,
                   extra_email_context=None):
    User = django.contrib.auth.get_user_model()

    response = django.contrib.auth.views.PasswordResetView(
        request, template_name, email_template_name,
        subject_template_name, password_reset_form, token_generator,
        post_reset_redirect, from_email, extra_context,
        html_email_template_name, extra_email_context)
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            signals.user_password_reset_request.send(
                sender=password_reset, request=request, user=user)
        except User.DoesNotExist:
            pass
    return response


class GenericLockedView(django.views.generic.FormView):
    template_name = accounts_settings.LOCKOUT_TEMPLATE
    form_class = forms.CaptchaForm
    urlPattern = ''

    def get_success_url(self):
        return django.urls.reverse_lazy(self.urlPattern)

    def form_valid(self, form):
        utils.reset(username=form.cleaned_data['username'])
        return super(GenericLockedView, self).form_valid(form)


class UserLockedOutView(GenericLockedView):
    urlPattern = 'login'


class AdminLockedOutView(GenericLockedView):
    urlPattern = 'admin:index'
