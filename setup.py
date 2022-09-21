#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
from setuptools import setup, find_packages


with open('accountsplus/__init__.py', 'r') as init_file:
    version = re.search('^__version__ = [\'"]([^\'"]+)[\'"]', init_file.read(), re.MULTILINE).group(1)

download_url = 'https://github.com/foundertherapy/django-users-plus/archive/{}.tar.gz'.format(version)

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-users-plus',
    version=version,
    packages=find_packages(),
    # license='MIT License',
    include_package_data=True,
    description=(
        'A django app that provides extra features including masquerading, local timezone support on users, '
        'an audit log for tracking admin and view-based data changes and activities, and support for Company '
        'models and added fields to User model.'
    ),
    url='http://github.com/foundertherapy/django-users-plus/',
    download_url=download_url,
    author='Dana Spiegel',
    author_email='dana@foundertherapy.co',
    keywords=['users', 'django', 'masquerading', 'masquerade', 'impersonate', 'timezone', 'company', 'audit log'],
)
