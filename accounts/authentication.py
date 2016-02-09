import rest_framework.authentication
import rest_framework.exceptions
import rest_framework.authtoken.models


class CachingTokenAuthentication(
        rest_framework.authentication.BaseAuthentication):
    """
    Simple token based authentication based on the default Django Rest Framework
    TokenAuthentication, but with superpowers (which is to cache the token in
    the Django cache).
    """

    model = rest_framework.authtoken.models.Token
    """
    A custom token model may be used, but must have the following properties.

    * key -- The string identifying the token
    * user -- The user to which the token belongs
    """

    def authenticate(self, request):
        auth = rest_framework.authentication.get_authorization_header(
            request).split()

        if not auth or auth[0].lower() != b'token':
            return None

        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise rest_framework.exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain ' \
                  'spaces.'
            raise rest_framework.exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(auth[1])

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
            raise rest_framework.exceptions.AuthenticationFailed(
                'Invalid token')

        if not token.user.is_active:
            raise rest_framework.exceptions.AuthenticationFailed(
                'User inactive or deleted')

        return token.user, token

    def authenticate_header(self, request):
        return 'Token'


