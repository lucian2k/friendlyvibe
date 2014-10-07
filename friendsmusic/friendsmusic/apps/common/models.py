from django.db import models
from django.contrib.auth.models import User
# from django_facebook.models import FacebookCustomUser

PROVIDER_YOUTUBE = 1
AVAIL_PROVIDERS = (
    (PROVIDER_YOUTUBE, 'Youtube'),
)


class Item(models.Model):
    provider = models.SmallIntegerField(choices=AVAIL_PROVIDERS, db_index=True)
    name = models.CharField(max_length=100)
    source_identifier = models.CharField(max_length=100, null=True, unique=True)

    def __unicode__(self):
        return u'Item id: %s, source id: %s' % (self.pk, self.source_identifier)

    def to_json(self):
        return {'title': self.name,
                'code': self.source_identifier,
                'permalink': self.permalink}

    @property
    def permalink(self):
        if self.provider == PROVIDER_YOUTUBE:
            return 'http://www.youtube.com/watch?v=%s' % self.source_identifier


class Playlist(models.Model):
    user = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    youtube_pl_id = models.CharField(max_length=50, null=True, unique=True)
    youtube_pl_name = models.CharField(max_length=50, null=True)
    youtube_json = models.TextField(null=True, blank=True)
    youtube_last_err = models.TextField(null=True, blank=True)
    is_private = models.BooleanField()

    def __unicode__(self):
        return u'Playlist ID: %s' % self.pk

    def to_model(self):
        return {'title': self.youtube_pl_name,
                'is_private': self.is_private}


class PlaylistItem(models.Model):
    wall_created = models.DateTimeField(db_index=True, auto_now=True)
    playlist_obj = models.ForeignKey(Playlist)
    item_obj = models.ForeignKey(Item)
    youtube_synced = models.DateTimeField(
        auto_now=False, auto_now_add=False, null=True)
    youtube_data = models.TextField(null=True)

    def __unicode__(self):
        return u'Playlist item: %s, user: %s' % (self.item_obj.source_identifier,
                                                self.playlist_obj.user)

