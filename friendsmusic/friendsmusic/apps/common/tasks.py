import urlparse
import datetime
import requests
import httplib2

from celery import task, subtask, group
from apiclient.discovery import build
from BeautifulSoup import BeautifulSoup
from oauth2client.client import AccessTokenCredentials

from django.conf import settings

from friendsmusic.apps.common.crawler import Crawler
from friendsmusic.apps.common.models import Item, Playlist, PlaylistItem, \
    PROVIDER_YOUTUBE


@task()
def sync_youtube_videos():
    playlist_users = Playlist.objects.exclude(youtube_pl_id__exact=None).\
        filter(youtube_last_err=None)
    for user_items in playlist_users:
        userobj = user_items.user.social_auth.get(provider='google-oauth2')
        credentials = AccessTokenCredentials(
            userobj.extra_data.get('access_token'), 'friendlyvibe/1.0')
        youtube = build('youtube', 'v3', http=credentials.authorize(httplib2.Http()))

        for plitem in user_items.playlistitem_set.filter(youtube_synced=None):
            video_add = youtube.playlistItems().insert(
                part="snippet",
                body=dict(
                    snippet=dict(
                        playlistId=user_items.youtube_pl_id,
                        resourceId=plitem.item_obj.source_identifier
                    )
                )
            ).execute()
            print video_add

        upload_items = user_items.playlistitem_set.filter(youtube_synced=None)
        print upload_items
    pass


@task()
def process_fb_feed(fb_token, user_obj, feed_extra_params={'limit': 100}):
    home_wall_req = requests.get('https://graph.facebook.com/me/home/', params={'access_token': fb_token})
    home_wall = home_wall_req.json()

    return [_extract_youtube_id(wall_item.get('link', None)) for wall_item in home_wall.get('data', []) if _is_song(wall_item)]


@task()
def video_map(videos_list, processing_callback, link):
    callback = subtask(processing_callback)
    return group(callback.clone([arg,], link=link) for arg in videos_list if arg)()


@task()
def check_video(yt_id, *args, **kwargs):
    """ See if the video is in the Music category """

    c = Crawler()
    page_content = c.fetchurl('http://www.youtube.com/watch?v=%s&gl=US' % yt_id)
    if not page_content:
        print 'Could not fetch http://www.youtube.com/watch?v=%s!' % yt_id
        return False, None, None

    soup = BeautifulSoup(page_content)

    extras = soup.find('ul', attrs = {'class' : 'watch-extras-section'})
    obj_title = soup.find('span', {'id': 'eow-title'})['title']

    # detect if the item is in the music category
    if '/music' in [t['href'] for t in extras.findAll('a')]:
        return True, yt_id, obj_title

    return False, None, None


@task()
def add_entry_playlist(video_check, user_obj):

    is_music, yt_id, obj_title = video_check

    if not is_music: return None

    playlist_item, item_created = Item.objects.get_or_create(source_identifier=yt_id,
                                                            provider=PROVIDER_YOUTUBE)
    playlist_item.name = obj_title
    playlist_item.save()

    # identify the user's playlist
    user_playlist, pl_created = Playlist.objects.get_or_create(user=user_obj)
    if not pl_created: # set last update to now
        user_playlist.last_update = datetime.datetime.now()
        user_playlist.save()

    # add the item to the user's playlist
    user_pl_item, upl_created = PlaylistItem.\
                        objects.get_or_create(playlist_obj=user_playlist,
                                              item_obj=playlist_item)

    print 'Added video %s to the user\'s %s playlist, yay!' % (yt_id, user_obj)
    return True


@task()
def check_video_old(yt_data):
    """ See if the video is about in the Music category item """

    youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_DEVELOPER_KEY)
    search_response = youtube.search().list(
        q='"%s"' % yt_data,
        part="id,snippet",
        maxResults=1
      ).execute()

    for search_result in search_response.get("items", []):
        print search_result

    return None


def _is_song(json_item):
    return True if 'youtube' in json_item.get('source', '') else False


def _youtube_search(yt_id):
    # use the api to do a video search

    return None


def _extract_youtube_id(link):
    if not link: return None

    url_data = urlparse.urlparse(link)
    query = urlparse.parse_qs(url_data.query)

    try: yt_id = query["v"][0]
    except: yt_id = None

    # parsing urls like http://youtu.be/WBKnpyoFEBo
    if yt_id is None and url_data.netloc == 'youtu.be':
        yt_id = url_data.path[1:]

    print 'Extracted %s from %s' % (yt_id, link)

    return yt_id
