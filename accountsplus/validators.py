from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
import re


class ComplexPasswordValidator(object):

    def validate(self, password, user=None):
        regex = '(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[$@#!%*?&])[A-Za-z\d$@#!%*?&]'
        if not re.match(regex, password):
             raise ValidationError(_('Password should contain uppercase, lowercase, numeric values and at least '
                                     'one of the following $@#!%*?&'), code='password_is_weak')

    def get_help_text(self):
         return _('Password should contain uppercase, lowercase, numeric values and at least '
                  'one of the following $@#!%*?&')


class CustomPasswordValidator(object):

    def validate(self, password, user=None):
        regex = '(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d\-\.\`\/\\#\^!\|~\*<>\?=\+@\{}_\$%\(\)\[]]*'
        if not re.match(regex, password):
             raise ValidationError(_('Must be 8 digits, including at least 1 uppercase letter and 1 number. Can include special characters.'), code='password_is_weak')

    def get_help_text(self):
         return _('Must be 8 digits, including at least 1 uppercase letter and 1 number. Can include special characters.')
