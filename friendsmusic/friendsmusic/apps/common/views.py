import simplejson
import time

from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.contrib.humanize.templatetags.humanize import naturaltime

from friendsmusic.apps.common import tasks
from friendsmusic.apps.common.models import Playlist, PlaylistItem
from friendsmusic.apps.common.decorators import render_json

def home(request):
	backends_connected = []
	if request.user.is_authenticated():
		backends_connected = [b.provider for b in request.user.social_auth.all()]

		# fb connected?
		if settings.BACKEND_FB_NAME in backends_connected:
			_update_playlist(request)

	# from bing import download_bing_wallpaper

	# gather information on the bing wallpaper data
	try: bing_wp_data = download_bing_wallpaper()
	except: bing_wp_data = None


	return render_to_response('home.html',
							  {'bing': bing_wp_data,
							  'backends_on': backends_connected})

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
