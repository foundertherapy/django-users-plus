from __future__ import unicode_literals

import django.core.exceptions
import django.shortcuts
import django.http
import django.forms
import django.core.exceptions
import django.contrib.admin
import django.contrib.admin.helpers
import django.contrib.admin.options
import django.contrib.admin.models
import django.contrib.auth.forms
import django.contrib.auth.admin
import django.utils.html
import django.template.response
import django.utils.decorators
import django.core.urlresolvers
import django.views.decorators.debug
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.apps import apps

import signals
import models


sensitive_post_parameters_m = django.utils.decorators.method_decorator(
    django.views.decorators.debug.sensitive_post_parameters())


class UserCreationForm(django.forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = django.forms.CharField(
        label=_("Password"),
        widget=django.forms.PasswordInput)
    password2 = django.forms.CharField(
        label=_("Password confirmation"),
        widget=django.forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = apps.get_model(settings.AUTH_USER_MODEL)
        fields = '__all__'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise django.forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(django.forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = django.contrib.auth.forms.ReadOnlyPasswordHashField(
        label=_('Password'),
        help_text=_('Raw passwords are not stored, so there is no way to see '
                    'this user\'s password, but you can change the password '
                    'using <a href="password/">this form</a>.'))

    class Meta:
        model = apps.get_model(settings.AUTH_USER_MODEL)
        fields = '__all__'

    def clean_password(self):
        return self.initial.get(
            'password',  apps.get_model(settings.AUTH_USER_MODEL).objects.make_random_password())


@django.contrib.admin.register(apps.get_model(settings.AUTH_USER_MODEL))
class UserAdmin(django.contrib.auth.admin.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = django.contrib.auth.forms.AdminPasswordChangeForm
    change_user_password_template = None
    list_display = ('email', 'masquerade', 'first_name', 'last_name',
                    'company', 'is_active', 'is_superuser', 'is_staff',
                    'get_timezone', 'last_login', )
    fieldsets = (
        (None, {
            'fields': ('email', 'password', 'first_name', 'last_name',
                       ),
        }),
        ('Company', {
            'fields': ('company', ),
        }),
        ('Preferences', {
            'fields': ('timezone', ),
        }),
        ('Security', {
            'fields': ('is_active', 'is_superuser', 'is_staff', 'groups',
                       'user_permissions', ),
        }),
        ('Important dates', {
            'fields': ('last_login', 'created_on', 'updated_on', ),
        }),
    )
    add_fieldsets = (
        (None, {
            'fields': ('email', 'password1', 'password2', 'first_name',
                       'last_name', ),
        }),
        ('Company', {
            'fields': ('company', ),
        }),
        ('Preferences', {
            'fields': ('timezone', ),
        }),
        ('Security', {
            'fields': ('is_active', 'is_superuser', 'is_staff', 'groups',
                       'user_permissions', ),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name', )
    ordering = ('email', )
    readonly_fields = ('last_login', 'created_on', 'updated_on', )
    actions = ('reset_passwords', )
    filter_horizontal = ('groups', 'user_permissions', )
    list_filter = ('is_active', )

    def queryset(self, request):
        queryset = super(UserAdmin, self).queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)
        return queryset

    def get_urls(self):
        from django.conf.urls import url
        return [
            url(r'^(\d+)/password/$',
             self.admin_site.admin_view(self.user_change_password))
        ] + super(UserAdmin, self).get_urls()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(UserAdmin, self).get_readonly_fields(
            request, obj)
        if not request.user.is_superuser:
            # ensure is_superuser is added to the readonly fields if the request
            # user isn't a superuser
            readonly_fields = list(readonly_fields)
            readonly_fields.append('is_superuser')
            readonly_fields = set(readonly_fields)
        return readonly_fields

    def log_addition(self, request, object, message):
        super(UserAdmin, self).log_addition(request, object, message)
        signals.user_create.send(
            sender=self.__class__, request=request, user=object)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        user = apps.get_model(settings.AUTH_USER_MODEL).objects.get(pk=object_id)
        old_email = user.email
        old_is_active = user.is_active

        response = super(UserAdmin, self).change_view(
            request, object_id, form_url, extra_context)

        if request.method == 'POST':
            # be sure to refresh the user since its likely changed
            user = apps.get_model(settings.AUTH_USER_MODEL).objects.get(pk=object_id)
            if user.email != old_email:
                signals.user_email_change.send(
                    sender=self.__class__, request=request, user=user,
                    old_email=old_email, new_email=user.email)
            if user.is_active != old_is_active:
                if user.is_active:
                    signals.user_activate.send(
                        sender=self.__class__, request=request, user=user)
                else:
                    signals.user_deactivate.send(
                        sender=self.__class__, request=request, user=user)
        return response

    def reset_user_password(self, request, user_id):
        if not self.has_change_permission(request):
            raise django.core.exceptions.PermissionDenied
        user = django.shortcuts.get_object_or_404(self.model, pk=user_id)

        form = django.contrib.auth.forms.PasswordResetForm(
            data={'email': user.email, })
        form.is_valid()

        form.save()
        self.message_user(
            request, 'Password reset email sent to {0}.'.format(user.email))

        signals.user_password_reset_request.send(
            sender=self.__class__, request=request, user=user)
        return django.http.HttpResponseRedirect('..')

    def reset_passwords(self, request, queryset):
        for user in queryset.all():
            self.reset_user_password(request, user.id)
    reset_passwords.short_description = 'Send password reset emails to ' \
                                        'selected Users'

    def get_timezone(self, obj):
        return unicode(obj.timezone)

    def masquerade(self, obj):
        return '<a href="{}">sign in</a>'.format(
            django.core.urlresolvers.reverse(
                'masquerade', kwargs={'user_id': obj.id}))
    masquerade.short_description = 'Sign in'
    masquerade.allow_tags = True

    @sensitive_post_parameters_m
    def user_change_password(self, request, id, form_url=''):
        if not self.has_change_permission(request):
            raise django.core.exceptions.PermissionDenied
        user = django.shortcuts.get_object_or_404(
            self.get_queryset(request), pk=id)
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                change_message = self.construct_change_message(
                    request, form, None)
                self.log_change(request, request.user, change_message)
                msg = _('Password changed successfully.')
                self.message_user(request, msg)
                return django.http.HttpResponseRedirect('..')
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': list(form.base_fields)})]
        adminForm = django.contrib.admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            'title': _('Change password: %s') % django.utils.html.escape(
                user.get_username()),
            'adminForm': adminForm,
            'form_url': form_url,
            'form': form,
            'is_popup':
            django.contrib.admin.options.IS_POPUP_VAR in request.REQUEST,
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
        }
        return django.template.response.TemplateResponse(
            request, self.change_user_password_template or
            'admin/auth/user/change_password.html',
            context, current_app=self.admin_site.name)


class ActionFilter(django.contrib.admin.SimpleListFilter):
    title = 'action'
    parameter_name = 'action_flag'

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(action_flag=self.value())
        else:
            return queryset

    def lookups(self, request, model_admin):
        return LogEntryAdmin.ACTION_NAMES.items()


@django.contrib.admin.register(django.contrib.admin.models.LogEntry)
class LogEntryAdmin(django.contrib.admin.ModelAdmin):
    ACTION_NAMES = {
        django.contrib.admin.models.ADDITION: 'ADD',
        django.contrib.admin.models.DELETION: 'DELETE',
        django.contrib.admin.models.CHANGE: 'CHANGE',
    }

    date_hierarchy = 'action_time'
    list_filter = (ActionFilter, 'content_type', 'user', )
    search_fields = ('object_repr', 'change_message', )
    list_display = ('action_time', 'user', 'content_type', 'object_link',
                    'action', 'change_message', )

    def get_readonly_fields(self, request, obj=None):
        return django.contrib.admin.models.LogEntry._meta.get_all_field_names()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        ct = obj.content_type
        repr_ = django.utils.html.escape(obj.object_repr)
        try:
            href = django.core.urlresolvers.reverse(
                'admin:{}_{}_change'.format(ct.app_label, ct.model),
                args=[obj.object_id])
            link = '<a href="{}">{}</a>'.format(href, repr_)
        except django.core.urlresolvers.NoReverseMatch:
            link = repr_
        return link if obj.action_flag != django.contrib.admin.models.DELETION \
            else repr_
    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = 'object'

    def queryset(self, request):
        return super(LogEntryAdmin, self).queryset(request).\
            prefetch_related('content_type')

    def action(self, obj):
        return self.ACTION_NAMES[obj.action_flag]
    action.short_description = 'Action'


@django.contrib.admin.register(models.Company)
class CompanyAdmin(django.contrib.admin.ModelAdmin):
    search_fields = ('name', )
    list_display = ('name', 'created_on', )
    readonly_fields = ('created_on', 'updated_on', )
    fields = ('created_on', 'updated_on', 'name',
              'street_address', 'street_address_2', 'city', 'state',
              'postal_code', )

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if 'name' in form.changed_data:
            signals.company_name_change.send(
                sender=self.__class__, request=request, user=request.user,
                company=obj, old_name=form.initial.get('name'), new_name=obj.name)
        super(CompanyAdmin, self).save_model(request, obj, form, change)


@django.contrib.admin.register(models.AuditLogEvent)
class AuditLogEventAdmin(django.contrib.admin.ModelAdmin):
    list_filter = ('company', )
    search_fields = ('user_email', 'message', )
    list_display = ('recorded_on', 'user', 'company',
                    'is_masquerading', 'masquerading_user',
                    'message', )
    ordering = ('-recorded_on', )
    list_per_page = 50
    fieldsets = (
        ('', {
            'fields': ('recorded_on', 'user_id', 'user_email', 'company', ),
        }),
        ('Masquerading User', {
            'fields': ('masquerading_user_email', 'masquerading_user_id', ),
        }),
        ('Audit Log Message', {
            'fields': ('message', ),
        }),
    )
    readonly_fields = ('created_on', 'updated_on', 'recorded_on', 'user_id',
                       'user_email', 'company', 'message',
                       'masquerading_user_email', 'masquerading_user_id', )
    actions = []

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def is_masquerading(self, obj):
        return obj.is_masquerading
    is_masquerading.boolean = True
    is_masquerading.short_description = 'Masquerade?'

    def user(self, obj):
        return '{}&nbsp;({})'.format(obj.user_email, obj.user_id)
    user.admin_order_field = 'user_id'
    user.allow_tags = True

    def masquerading_user(self, obj):
        if obj.is_masquerading:
            return '{}&nbsp;({})'.format(
                obj.masquerading_user_email, obj.masquerading_user_id)
        else:
            return ''
    masquerading_user.short_description = 'Masquerading User'
    masquerading_user.admin_order_field = 'masquerading_user_id'
    masquerading_user.allow_tags = True
