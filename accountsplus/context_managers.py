from __future__ import unicode_literals

from contextlib import contextmanager

from django.utils import translation


@contextmanager
def language(lang):
    old_language = translation.get_language()
    try:
        translation.activate(lang)
        yield
    finally:
        translation.activate(old_language)
