from .. import validators
from django.core.exceptions import ValidationError
from django.test import TestCase


class PasswordValidatorTestCase(TestCase):
    def validate_password(self, password):
        validator = validators.ComplexPasswordValidator()
        try:
            validator.validate(password)
        except ValidationError:
            return False
        else:
            return True

    def test_password_missing_special_char(self):
        self.assertFalse(self.validate_password('aab1234AAAA'))

    def test_password_missing_numeric(self):
        self.assertFalse(self.validate_password('aab$$$$AAAA'))

    def test_password_missing_lower(self):
        self.assertFalse(self.validate_password('$$$$1234AAAA'))

    def test_password_missing_upper(self):
        self.assertFalse(self.validate_password('aab1234$$$$'))

    def test_good_password(self):
        self.assertTrue(self.validate_password('aab1234AAAA$#'))
