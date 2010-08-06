from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root),
    #(r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^account/', include('account.urls')),
    (r'^distribution/', include('distribution.urls')),
    (r'^customer/', include('customer.urls')),
    url(r'^nopermissions/$', direct_to_template, {"template":"account/no_permissions.html"},
        name="no_permissions"),
)
                           

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': '/home/bob/foodnetwork/media', 'show_indexes': True}),
    )
