from django.conf.urls import patterns, include, url
from VideoApp.views import *
from VideoSite.settings import *

from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'VideoSite.views.home', name='home'),
    # url(r'^VideoSite/', include('VideoSite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^video/$', video),
    url(r'^version/$', version),
    url(r'^seeders/(.+)/$', seeders),
)

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
