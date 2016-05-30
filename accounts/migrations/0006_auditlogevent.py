# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20150513_2100'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLogEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('recorded_on', models.DateTimeField(auto_now_add=True)),
                ('user_id', models.IntegerField(verbose_name='User ID', db_index=True)),
                ('user_email', models.EmailField(max_length=75, verbose_name='User Email', db_index=True)),
                ('message', models.TextField(verbose_name='Audit Message')),
                ('masquerading_user_id', models.IntegerField(db_index=True, null=True, verbose_name='Masquerading User ID', blank=True)),
                ('masquerading_user_email', models.EmailField(db_index=True, max_length=75, verbose_name='Masquerading User Email', blank=True)),
                ('company', models.ForeignKey(to='accounts.Company')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
