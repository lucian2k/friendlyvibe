from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'friendsmusic.apps.common.views.home', name='home'),
    url(r'^go/$', 'friendsmusic.apps.common.views.welcome', name='welcome'),
    url(r'^go/json-playlist$', 'friendsmusic.apps.common.views.json_playlist', name='json_playlist'),
    (r'^fb/', include('django_facebook.urls')),
    url(r'^logout/$', 'friendsmusic.apps.common.views.logout_view', name='logout'),
    # (r'^accounts/', include('django_facebook.auth_urls'))
    # url(r'^friendsmusic/', include('friendsmusic.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
