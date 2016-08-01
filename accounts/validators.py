from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
import re


class ComplexPasswordValidator(object):

    def validate(self, password, user=None):
        regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[$@$!%*?&])[A-Za-z\d$@$!%*?&]"
        if not re.match(regex, password):
             raise ValidationError(_("Password should contain capital and small letters, numeric values and "
                                     "one of the following $@$!%*?&"), code='password_is_weak',)

    def get_help_text(self):
         return _("Password should contain capital and small letters, numeric values and one of the following $@$!%*?&")
