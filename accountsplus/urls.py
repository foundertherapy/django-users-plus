import django.contrib.auth.urls
import django.contrib.auth.views
from django.urls import include, path, re_path

from accountsplus import views
from accountsplus import forms

urlpatterns = [
    path('logout/', views.logout_then_login, name='logout'),
    path('password_change/', views.password_change, name='password_change'),
    path('password_reset/', views.password_reset, name='password_reset'),
    # override the admin password reset flow to use the normal site password
    # reset flow
    path('password_reset/', views.password_reset, name='admin_password_reset'),
    re_path(
        r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        django.contrib.auth.views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'login/',
        django.contrib.auth.views.LoginView.as_view(
            authentication_form=forms.EmailBasedAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('', include(django.contrib.auth.urls)),
    # masquerade views
    path('admin/masquerade/end/', views.EndMasqueradeUserView.as_view(), name='end_masquerade'),
    path('admin/masquerade/<int:user_id>/', views.MasqueradeUserView.as_view(), name='masquerade'),
]
