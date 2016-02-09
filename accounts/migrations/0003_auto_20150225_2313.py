# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def add_company_example(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Company = apps.get_model("accounts", "Company")
    company = Company(name='Example')
    company.save()


def remove_companies(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Company = apps.get_model("accounts", "Company")
    company = Company.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20140924_1347'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Company',
                'verbose_name_plural': 'Companies',
            },
            bases=(models.Model,),
        ),
        migrations.RunPython(add_company_example, remove_companies),
        migrations.AddField(
            model_name='user',
            name='company',
            field=models.ForeignKey(related_name='users', default=1, to='accounts.Company'),
            preserve_default=False,
        ),
    ]
