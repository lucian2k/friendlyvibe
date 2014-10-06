import simplejson
import httplib2
import datetime

from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.views.decorators.csrf import csrf_exempt

from apiclient.discovery import build
from oauth2client.client import AccessTokenCredentials

from friendsmusic.apps.common import tasks
from friendsmusic.apps.common.models import Playlist, PlaylistItem
from friendsmusic.apps.common.decorators import render_json


def home(request):
    backends_connected = []
    playlist = None

    if request.user.is_authenticated():
        backends_connected = [b.provider for b in request.user.social_auth.all()]

        # fb connected?
        if settings.BACKEND_FB_NAME in backends_connected:
            _update_playlist(request)

        # playlist info
        playlist = None
        try:
            playlist = Playlist.objects.get(user=request.user)
        except:
            pass

    return render_to_response('home.html',
                              {'backends_on': backends_connected,
                               'playlist_obj': playlist,
                               'default_plname': settings.DEFAULT_YOUTUBE_PLNAME},
                              RequestContext(request))


@csrf_exempt
@render_json()
def playlist(request):
    if request.method == 'POST':
        playlist_result = _create_remote_playlist(request)

        playlist = playlist_result.get('playlist_obj').to_model()
        playlist['error'] = playlist_result.get('error')
    else:
        try:
            playlist = Playlist.objects.get(user=request.user).to_model()
        except:
            playlist = {'title': settings.DEFAULT_YOUTUBE_PLNAME,
                        'is_private': False}

    return playlist


def _create_remote_playlist(request):
    # cheking the local playlist
    result = {'error': None, 'playlist_obj': None}
    try:
        youtube_obj = request.user.social_auth.get(provider='google-oauth2')
    except:
        return result

    user_playlist, pl_created = \
        Playlist.objects.get_or_create(user=request.user)
    if not pl_created: # set last update to now
        user_playlist.last_update = datetime.datetime.now()
        user_playlist.save()
    else:
        user_playlist.youtube_pl_name = settings.DEFAULT_YOUTUBE_PLNAME
        user_playlist.save()
    result['playlist_obj'] = user_playlist

    if user_playlist.youtube_pl_id is None and request.method == 'POST':
        post_data = simplejson.loads(request.body)
        credentials = AccessTokenCredentials(
            youtube_obj.extra_data.get('access_token'), 'friendlyvibe/1.0')
        youtube = build('youtube', 'v3', http=credentials.authorize(httplib2.Http()))

        try:
            new_playlist = youtube.playlists().insert(
                part="snippet,status",
                body=dict(
                    snippet=dict(
                        title=settings.DEFAULT_YOUTUBE_PLNAME,
                        description="A playlist automatically created and managed by friendlyvibe.com"
                    ),
                    status=dict(
                        privacyStatus='private' if post_data.get('is_private') is not False else 'public'
                    )
                )
            ).execute()

            user_playlist.youtube_json = simplejson.dumps(new_playlist)
            user_playlist.youtube_pl_id = new_playlist.get(u'id')
            user_playlist.youtube_pl_name = post_data.get('title')
            user_playlist.is_private = False if post_data.get('is_private') is None else True
            user_playlist.save()

        except Exception, e:
            # do some signal here to KNOW the user's youtube account is disconnected
            result['error'] = str(e)

    return result


def _update_playlist(request):
    # check if there's an update
    cache_key = ('fb_update_timeout_%s') % request.user
    if not cache.get(cache_key):
        # look into the user's fb account
        social_obj = request.user.social_auth.get(provider='facebook')
        access_token = social_obj.extra_data.get('access_token')

        chain = tasks.process_fb_feed.s(access_token, request.user) | \
            tasks.video_map.s(tasks.check_video.s(),
                              link=tasks.add_entry_playlist.s(request.user))
        chain()

        cache.set(cache_key, True, settings.FB_UPDATE_MIN_INTERVAL)


@login_required
@render_json()
def social_items(request):
    try:
        playlist = Playlist.objects.get(user=request.user)
    except:
        return []

    return [i.item_obj.to_model() for i in playlist.playlistitem_set.all()]


@login_required
def welcome(request):
    context = RequestContext(request)

    # try to update the playlist
    # _update_playlist(request)
    tasks.sync_youtube_videos.delay()

    return render_to_response('playlist.html', context)


@render_json()
@login_required
def json_playlist(request):
    last_item = request.GET.get('lu', 0) # signals that we should return only earlier items

    playlist_items = PlaylistItem.objects.filter(
        playlist_obj__user=request.user).order_by('-wall_created')
    if last_item:
        try:
            playlist_items = playlist_items.filter(pk__gt=int(last_item))
        except:
            pass

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
