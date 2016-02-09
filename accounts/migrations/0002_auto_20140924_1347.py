# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import timezone_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_squashed_0006_user_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='timezone',
            field=timezone_field.fields.TimeZoneField(default='America/New_York', max_length=63),
        ),
    ]
