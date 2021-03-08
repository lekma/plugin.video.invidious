# -*- coding: utf-8 -*-


from iapc import Client

from tools import Logger

from . import __trending_types__
from .objects import Channel, Channels, Playlists, Video, Videos


# ------------------------------------------------------------------------------
# InvidiousClient

class InvidiousClient(object):

    __defaults__ = {
        "playlists": {
            "playlists": [],
            "continuation": None
        },
        "playlist": {
            "videos": [],
            "title": None,
            "authorId": None
        }
    }

    __search__ = {
        "channel": Channels,
        "playlist": Playlists,
        "video": Videos
    }

    def __init__(self):
        self.logger = Logger(component="client")
        self.__client__ = Client()

    # --------------------------------------------------------------------------

    def __query__(self, key, *args, **kwargs):
        return (
            self.__client__.query(key, *args, **kwargs) or
            self.__defaults__.get(key, [])
        )

    def __channel__(self, authorId):
        return Channel(self.__client__.channel(authorId))

    # --------------------------------------------------------------------------

    def pushQuery(self, query):
        self.__client__.pushQuery(query)

    def instances(self, **kwargs):
        return [
            instance[0] for instance in self.__client__.instances(**kwargs)
            if instance[1]["type"] in ("http", "https")
        ]

    # --------------------------------------------------------------------------

    def video(self, **kwargs):
        video, headers = self.__client__.video(kwargs.pop("videoId"), **kwargs)
        if (video := Video(video)):
            url, manifestType, mimeType = (
                video.dashUrl, "mpd", "video/vnd.mpeg.dash.mpd"
            )
            if video.liveNow and hasattr(video, "hlsUrl"):
                url, manifestType, mimeType = (
                    video.hlsUrl, "hls", "application/vnd.apple.mpegurl"
                )
            self.logger.info(f"video: {url}")
            return (
                (video.makeItem(url), manifestType),
                {"mimeType": mimeType, "headers": headers}
            )
        return (None, None)

    def channel(self, page=1, limit=60, **kwargs):
        category = None
        authorId = kwargs.pop("authorId")
        data = self.__query__("videos", authorId, page=page, **kwargs)
        if (channel := self.__channel__(authorId)):
            category = channel.author
            if channel.autoGenerated:
                limit = 0
        return Videos(data, limit=limit, category=category)

    def playlist(self, page=1, limit=100, **kwargs):
        data = self.__query__(
            "playlist", kwargs.pop("playlistId"), page=page, **kwargs
        )
        if (authorId := data.get("authorId")):
            if (channel := self.__channel__(authorId)) and channel.autoGenerated:
                limit = 0
        return Videos(data["videos"], limit=limit, category=data["title"])

    # feed ---------------------------------------------------------------------

    def feed(self, ids, page=1, **kwargs):
        data, limit = self.__client__.feed(ids, page=page, **kwargs)
        return Videos(data, limit=limit)

    # top ----------------------------------------------------------------------

    #def top(self, **kwargs):
    #    return Videos(self.__query__("top", **kwargs))

    # popular ------------------------------------------------------------------

    def popular(self, **kwargs):
        return Videos(self.__query__("popular", **kwargs))

    # trending -----------------------------------------------------------------

    def trending(self, **kwargs):
        return Videos(
            self.__query__("trending", **kwargs),
            category=__trending_types__.get(kwargs.get("type"))
        )

    # playlists ----------------------------------------------------------------

    def playlists(self, **kwargs):
        category = None
        authorId = kwargs.pop("authorId")
        data = self.__query__("playlists", authorId, **kwargs)
        if (channel := self.__channel__(authorId)):
            category = channel.author
            if channel.autoGenerated:
                data["continuation"] = None
        return Playlists(
            data["playlists"], continuation=data["continuation"],
            category=category
        )

    # autogenerated ------------------------------------------------------------

    def autogenerated(self, **kwargs):
        category = None
        authorId = kwargs.pop("authorId")
        data = self.__client__.autogenerated(authorId, **kwargs)
        if (channel := self.__channel__(authorId)):
            category = channel.author
        return Playlists(data, category=category)

    # search -------------------------------------------------------------------

    def search(self, query, page=1, limit=20, **kwargs):
        return self.__search__[kwargs["type"]](
            self.__query__("search", q=query, page=page, **kwargs),
            limit=limit, category=query
        )


client = InvidiousClient()

