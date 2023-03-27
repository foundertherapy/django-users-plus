import django.conf.urls
import django.contrib.admin


urlpatterns = [
    django.conf.urls.url(r'^', django.conf.urls.include('accountsplus.urls')),
    django.conf.urls.url(r'^admin/', django.contrib.admin.site.urls),
]
