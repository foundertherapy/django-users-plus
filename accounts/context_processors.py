from __future__ import unicode_literals


def masquerade_info(request):
    if request.user.is_authenticated():
        return {
            'is_masquerading': request.session.get('is_masquerading', False),
        }
    else:
        return {
            'is_masquerading': False,
        }
