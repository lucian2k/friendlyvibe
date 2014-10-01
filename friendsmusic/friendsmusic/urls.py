from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'friendsmusic.apps.common.views.home', name='home'),
    url(r'^go/$', 'friendsmusic.apps.common.views.welcome', name='welcome'),
    url(r'^go/json-playlist$', 'friendsmusic.apps.common.views.json_playlist', name='json_playlist'),
    url(r'^logout/$', 'friendsmusic.apps.common.views.logout_view', name='logout'),
    url(r'^playlist/$', 'friendsmusic.apps.common.views.playlist', name='playlist'),
    url(r'^items/$', 'friendsmusic.apps.common.views.social_items', name='items'),
    url('', include('social.apps.django_app.urls', namespace='social')),
    # url(r'^friendsmusic/', include('friendsmusic.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
