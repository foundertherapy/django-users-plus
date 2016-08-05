from __future__ import unicode_literals

import django.test
import django.contrib.admin

import logging

from .. import admin
from test_models import (UnitTestCompany, UnitTestUser, UnitTestAuditLogEvent, )


logging.disable(logging.CRITICAL)


@django.contrib.admin.register(UnitTestCompany)
class UnitTestCompanyAdmin(admin.BaseCompanyAdmin):
    pass


@django.contrib.admin.register(UnitTestUser)
class UnitTestUserAdmin(admin.BaseUserAdmin):
    pass


@django.contrib.admin.register(UnitTestAuditLogEvent)
class UnitTestAuditLogEventAdmin(admin.BaseAuditLogEventAdmin):
    pass
