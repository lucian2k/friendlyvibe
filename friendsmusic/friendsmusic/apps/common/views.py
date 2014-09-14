import simplejson
import time
import httplib2
import datetime

from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.contrib.humanize.templatetags.humanize import naturaltime

from apiclient.discovery import build
from oauth2client.client import AccessTokenCredentials

from friendsmusic.apps.common import tasks
from friendsmusic.apps.common.models import Playlist, PlaylistItem
from friendsmusic.apps.common.decorators import render_json

def home(request):
    backends_connected = []
    playlist = None

    if request.user.is_authenticated():
        _create_remote_playlist(request)
        backends_connected = [b.provider for b in request.user.social_auth.all()]

        # fb connected?
        if settings.BACKEND_FB_NAME in backends_connected:
            _update_playlist(request)

        # playlist info
        playlist = Playlist.objects.get(user=request.user)
        # youtube playlist not here - create it

    return render_to_response('home.html',
                              {'backends_on': backends_connected,
                              'playlist_obj': playlist,
                              'default_plname': settings.DEFAULT_YOUTUBE_PLNAME},
                              RequestContext(request))

def _create_remote_playlist(request):
    # chaking the local playlist
    user_playlist, pl_created = Playlist.objects.get_or_create(user=request.user)
    if not pl_created: # set last update to now
        user_playlist.last_update = datetime.datetime.now()
        user_playlist.save()

    if user_playlist.youtube_pl_id is None:
        youtube_obj = request.user.social_auth.get(provider='google-oauth2')
        credentials = AccessTokenCredentials(
            youtube_obj.extra_data.get('access_token'), 'friendlyvibe/1.0')
        youtube = build('youtube', 'v3', http=credentials.authorize(httplib2.Http()))
        try:
            new_playlist = youtube.playlists().insert(
                part="snippet,status",
                body=dict(
                    snippet=dict(
                        title=setting.DEFAULT_YOUTUBE_PLNAME,
                        description="A playlist automatically created and updated by friendlyvibe.com"
                    ),
                status=dict(
                    privacyStatus="private"
                )
            ))
        except Exception, e:
            print str(e)
        print youtube.playlists().list(part='id', mine=True).execute()

def _update_playlist(request):
    # check if there's an update
    cache_key = ('fb_update_timeout_%s') % request.user
    cache_key = None
    if not cache.get(cache_key):
        # look into the user's fb account
        social_obj = request.user.social_auth.get(provider='facebook')
        access_token = social_obj.extra_data.get('access_token')

        # open_fb_obj = api.get_facebook_graph(request, request.user.access_token)
        chain = tasks.process_fb_feed.s(access_token, request.user) | \
                tasks.video_map.s(tasks.check_video.s(), link=tasks.add_entry_playlist.s(request.user))
        chain()

        # cache.set(cache_key, True, settings.FB_UPDATE_MIN_INTERVAL)


@login_required
def welcome(request):
    context = RequestContext(request)

    # try to update the playlist
    _update_playlist(request)

    return render_to_response('playlist.html', context)

@render_json()
@login_required
def json_playlist(request):
    last_item = request.GET.get('lu', 0) # signals that we should return only earlier items

    playlist_items = PlaylistItem.objects.filter(playlist_obj__user=request.user)\
                                                    .order_by('-wall_created')
    if last_item:
        try: playlist_items = playlist_items.filter(pk__gt=int(last_item))
        except: pass

    last_update = None
    try:
        last_update = Playlist.objects.get(user=request.user).last_update
    except:
        pass

    # try to update the playlist
    _update_playlist(request)

    return {'results': [i.item_obj.to_json() for i in playlist_items],
            'update_item': playlist_items[0].pk if len(playlist_items) > 0 else last_item,
            'last_update_human': naturaltime(last_update),
            'last_update': last_update.strftime('%s') if last_update else None}

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')
