# -*- coding: utf-8 -*-


from urllib.parse import quote_plus

from nuttig import (
    buildUrl, getAddonId, getCondition, getSetting,
    localizedString, maybeLocalize, ListItem
)
from nuttig.objects import List, Object

from invidious.search import queryType, querySort


# ------------------------------------------------------------------------------
# Items

class Item(Object):

    __menus__ = []

    @classmethod
    def __condition__(cls, args, expected):
        result = getSetting(*args) if (len(args) > 1) else getCondition(*args)
        return (result == expected)

    @classmethod
    def menus(cls, **kwargs):
        return [
            (
                maybeLocalize(label).format(**kwargs),
                action.format(
                    addonId=getAddonId(),
                    **{key: quote_plus(value) for key, value in kwargs.items()}
                )
            )
            for label, action, *conditions in cls.__menus__
            if all(cls.__condition__(*condition) for condition in conditions)
        ]

    def __infos__(self, *args):
        for arg in args:
            if (attr := getattr(self, arg, None)):
                yield f"{attr}"

    @property
    def thumbnail(self):
        return self.get("thumbnail", self.__thumbnail__)

    @property
    def poster(self):
        return self.get("poster", self.__thumbnail__)

    @property
    def icon(self):
        return self.get("icon", self.__thumbnail__)

    def labels(self, title, plot, **kwargs):
        return dict(video=dict(title=title, plot=plot, **kwargs))


class Items(List):

    __ctor__ = Item

    def __init__(self, items, previous=None, next=None, **kwargs):
        super(Items, self).__init__(items, **kwargs)
        self.previous = previous
        self.next = next


class Contents(Items):

    def __init__(self, items, **kwargs):
        super(Contents, self).__init__(items, content="videos", **kwargs)


# ------------------------------------------------------------------------------
# Folders

class Folder(Item):

    __thumbnail__ = "DefaultFolder.png"

    @property
    def action(self):
        return self.get("action", self.type)

    @property
    def properties(self):
        return self.get("properties")

    @property
    def plot(self):
        if (plot := self.get("plot")):
            return maybeLocalize(plot)

    @property
    def art(self):
        return dict(
            {"poster": self.poster, "icon": self.icon}, **self.get("art", {})
        )

    def getItem(self, url, **kwargs):
        title = maybeLocalize(self.title)
        return ListItem(
            title,
            buildUrl(url, action=self.action, **dict(self.kwargs, **kwargs)),
            isFolder=True,
            properties=self.properties,
            infoLabels=self.labels(title, self.plot or title),
            **self.art
        )


class Folders(Items):

    __ctor__ = Folder


# ------------------------------------------------------------------------------
# Queries

class Query(Item):

    __menus__ = [
        (60101, "RunScript({addonId},updateQueryType,{q})"),
        (60102, "RunScript({addonId},updateQuerySort,{q})"),
        (60103, "RunScript({addonId},removeQuery,{q})"),
        (60104, "RunScript({addonId},clearHistory)")
    ]

    __thumbnail__ = "DefaultAddonsSearch.png"

    __thumbnails__ = {
        "all": "DefaultAddonsSearch.png",
        "video": "DefaultAddonVideo.png",
        "channel": "DefaultArtist.png",
        "playlist": "DefaultPlaylist.png",
        "movie": "DefaultMovies.png",
        "show": "DefaultTVShows.png"
    }

    @property
    def thumbnail(self):
        return self.__thumbnails__.get(self.type, self.__thumbnail__)

    def getItem(self, url):
        return ListItem(
            self.q,
            buildUrl(
                url,
                action="search",
                q=self.q,
                type=self.type,
                sort=self.sort
            ),
            isFolder=True,
            infoLabels=self.labels(self.q, self.q),
            contextMenus=self.menus(
                q=self.q,
                _type_=localizedString(queryType[self.type]),
                _sort_=localizedString(querySort[self.sort])
            ),
            thumb=self.thumbnail
        )


class Queries(Items):

    __ctor__ = Query


# ------------------------------------------------------------------------------
# Videos

class Video(Item):

    __menus__ = [
        (
            43210, "RunScript({addonId},playFromYouTube,{videoId})",
            (("context.fromyoutube", bool), True),
            (("System.AddonIsEnabled(service.yt-dlp)",), True)
        ),
        (
            43220, "RunScript({addonId},playWithYouTube,{videoId})",
            (("context.withyoutube", bool), True)
        ),
        (60201, "RunScript({addonId},goToChannel,{channelId})"),
        (
            60202,
            "RunScript({addonId},addChannelToFeed,{channelId},{channel})",
            (("home.feed", bool), True)
        )
    ]

    __thumbnail__ = "DefaultAddonVideo.png"

    @property
    def live(self):
        return self.get("live", False)

    @property
    def title(self):
        if self.live:
            return " ".join(("[COLOR red](₍.₎)[/COLOR]", self.get("title")))
        return self.get("title")

    @property
    def _infos_(self):
        return " • ".join(list(self.__infos__("viewsText", "likesText")))

    @property
    def infos(self):
        return "\n".join(list(self.__infos__("_infos_", "publishedText")))

    @property
    def plot(self):
        return "\n\n".join(
            self.__infos__("title", "channel", "infos", "description")
        )

    @property
    def duration(self):
        return self.get("duration", -1)

    def labels(self, *args, **kwargs):
        if self.live:
            kwargs["playcount"] = 0
        return super(Video, self).labels(*args, **kwargs)

    def makeItem(self, path):
        return ListItem(
            self.title,
            path,
            infoLabels=self.labels(self.title, self.plot, mediatype="video"),
            streamInfos={
                "video": {
                    "duration": self.duration
                }
            },
            contextMenus=self.menus(
                videoId=self.videoId,
                channelId=self.channelId,
                channel=self.channel
            ),
            thumb=self.thumbnail
        )

    def getItem(self, url):
        return self.makeItem(buildUrl(url, action="play", videoId=self.videoId))


class Videos(Contents):

    __ctor__ = Video


# ------------------------------------------------------------------------------
# Channels

class BaseChannel(Item):

    __thumbnail__ = "DefaultArtist.png"

    @property
    def plot(self):
        return "\n\n".join(
            self.__infos__("channel", "subscribersText", "description")
        )

    def getItem(self, url):
        return ListItem(
            self.channel,
            buildUrl(url, action="channel", channelId=self.channelId),
            isFolder=True,
            infoLabels=self.labels(self.channel, self.plot),
            contextMenus=self.menus(
                channelId=self.channelId,
                channel=self.channel
            ),
            thumb=self.thumbnail
        )


class Channel(BaseChannel):

    __menus__ = [
        (
            60202,
            "RunScript({addonId},addChannelToFeed,{channelId},{channel})",
            (("home.feed", bool), True)
        )
    ]

class Channels(Contents):

    __ctor__ = Channel


class FeedChannel(BaseChannel):

    __menus__ = [
        (60301, "RunScript({addonId},removeChannelFromFeed,{channelId})"),
        (60302, "RunScript({addonId},clearChannelsFromFeed)")
    ]

class FeedChannels(Contents):

    __ctor__ = FeedChannel


# ------------------------------------------------------------------------------
# Playlists

class Playlist(Item):

    __menus__ = [
        (60201, "RunScript({addonId},goToChannel,{channelId})"),
        (
            60202,
            "RunScript({addonId},addChannelToFeed,{channelId},{channel})",
            (("home.feed", bool), True)
        )
    ]

    __thumbnail__ = "DefaultPlaylist.png"

    @property
    def _infos_(self):
        return " • ".join(list(self.__infos__("viewsText", "videosText")))

    @property
    def infos(self):
        return "\n".join(list(self.__infos__("_infos_", "updatedText")))

    @property
    def plot(self):
        return "\n\n".join(
            self.__infos__("title", "channel", "infos", "description")
        )

    def getItem(self, url):
        return ListItem(
            self.title,
            buildUrl(url, action="playlist", playlistId=self.playlistId),
            isFolder=True,
            infoLabels=self.labels(self.title, self.plot),
            contextMenus=self.menus(
                playlistId=self.playlistId,
                channelId=self.channelId,
                channel=self.channel
            ),
            thumb=self.thumbnail
        )


class Playlists(Contents):

    __ctor__ = Playlist


# ------------------------------------------------------------------------------
# Results

class Results(Contents):

    __ctor__ = None

    __types__ = {
        "video": Video,
        "channel": Channel,
        "playlist": Playlist
    }

    def __init__(self, items, **kwargs):
        super(Results, self).__init__(
            (self.__types__[item["type"]](item) for item in items if item),
            **kwargs
        )
