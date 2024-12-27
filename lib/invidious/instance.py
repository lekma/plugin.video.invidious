# -*- coding: utf-8 -*-


from functools import wraps
from time import time
from urllib.parse import urlsplit, urlunsplit

from requests import HTTPError

from xbmcgui import ALPHANUM_HIDE_INPUT

from iapc import public
from nuttig import (
    buildUrl, getSetting, maybeLocalize, setSetting,
    inputDialog, okDialog, selectDialog
)

from invidious.extract import (
    IVChannel, IVPlaylist, IVPlaylists, IVResults, IVVideo, IVVideos
)
from invidious.regional import locales, regions
from invidious.session import IVSession
from invidious.ytdlp import YtDlp


# cached -----------------------------------------------------------------------

def cached(name):
    def decorator(func):
        @wraps(func)
        def wrapper(self, key, *args, **kwargs):
            cache = self.__cache__.setdefault(name, {})
            if (
                (not (value := cache.get(key))) or
                (
                    (expires := getattr(value, "__expires__", None)) and
                    (time() >= expires)
                )
            ):
                value = cache[key] = func(self, *(args or (key,)), **kwargs)
            return value
        return wrapper
    return decorator


# ------------------------------------------------------------------------------
# IVInstance

class IVInstance(object):

    __headers__ = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "*"
    }

    def __init__(self, logger):
        self.logger = logger.getLogger(f"{logger.component}.instance")
        self.__session__ = IVSession(self.logger, headers=self.__headers__)
        self.__ytdlp__ = YtDlp(self.logger)
        self.__cache__ = {}

    def __setup__(self):
        if (uri := getSetting("instance.uri", str)):
            self.__scheme__, self.__netloc__, *unused = urlsplit(uri)
            self.__url__ = buildUrl(uri, getSetting("instance.path", str))
            self.__uri__ = urlunsplit(
                (self.__scheme__, self.__netloc__, "", "", "")
            )
        else:
            self.__scheme__ = self.__netloc__ = self.__url__ = self.__uri__ = None
        self.__proxy__ = getSetting("instance.proxy", bool)
        self.__locale__ = getSetting("regional.locale", str)
        self.__region__ = getSetting("regional.region", str)
        settings = (
            #("Uri", self.__uri__),
            ("Url", self.__url__),
            (41130, self.__proxy__),
            (
                41211,
                f"({self.__locale__}) {getSetting('regional.locale.text', str)}"
            ),
            (
                41221,
                f"({self.__region__}) {getSetting('regional.region.text', str)}"
            )
        )
        for label, setting in settings:
            self.logger.info(f"{maybeLocalize(label)}: {setting}")
        self.__session__.__setup__()
        self.__ytdlp__.__setup__()
        self.__cache__.clear()

    def __stop__(self):
        self.__cache__.clear()
        self.__ytdlp__.__stop__()
        self.__session__.__stop__()
        self.logger.info("stopped")

    # instance -----------------------------------------------------------------

    def __instances__(self):
        return self.__session__.__get__(
            "https://api.invidious.io/instances.json", sort_by="location"
        )

    def instances(self):
        return {
            instance["uri"]: f"({instance['region']})\t{name}"
            for name, instance in self.__instances__()
            if (instance["api"] and (instance["type"] in ("http", "https")))
        }

    @public
    def instance(self):
        return self.__url__

    @public
    def selectInstance(self):
        if (instances := self.instances()):
            uri = getSetting("instance.uri", str)
            keys = list(instances.keys())
            values = list(instances.values())
            preselect = keys.index(uri) if uri in keys else -1
            index = selectDialog(values, heading=41113, preselect=preselect)
            if index > -1:
                setSetting("instance.uri", keys[index], str)
                return True
        else:
            okDialog(maybeLocalize(90101))
        return False

    # region -------------------------------------------------------------------

    def __select__(self, ordered, setting, heading):
        keys = list(ordered.keys())
        values = list(ordered.values())
        if (
            (
                index := selectDialog(
                    [f"({k}) {v}" for k, v in ordered.items()],
                    preselect=(
                        keys.index(current)
                        if (current := getSetting(setting, str)) in ordered
                        else -1
                    ),
                    heading=heading
                )
            ) > -1
        ):
            setSetting(setting, keys[index], str)
            setSetting(f"{setting}.text", values[index], str)

    @public
    def selectLocale(self):
        self.__select__(locales, "regional.locale", 41212)

    @public
    def selectRegion(self):
        self.__select__(regions, "regional.region", 41222)

    # tokens -------------------------------------------------------------------

    #@public
    #def addApiToken(self):
    #    self.logger.info(f"addApiToken()")
    #    if (
    #        (uri := inputDialog(heading=90007, defaultt=self.__uri__)) and
    #        (email := inputDialog(heading=90008)) and
    #        (password := inputDialog(heading=90009, option=ALPHANUM_HIDE_INPUT))
    #    ):
    #        self.__tokens__.registerToken(uri, email, password)

    #@public
    #def removeApiTokens(self):
    #    self.logger.info(f"removeApiTokens()")

    # --------------------------------------------------------------------------

    def __regional__(self, regional, kwargs):
        kwargs["hl"] = self.__locale__
        if regional:
            kwargs["region"] = self.__region__
        elif "region" in kwargs:
            del kwargs["region"]

    __paths__ = {
        "video": "videos/{}",
        "channel": "channels/{}",
        "playlist": "playlists/{}",
        "videos": "channels/{}/videos",
        "playlists": "channels/{}/playlists",
        "streams": "channels/{}/streams",
        "shorts": "channels/{}/shorts"
    }

    def __buildUrl__(self, key, *arg):# *arg is a trick
        return buildUrl(self.__url__, self.__paths__.get(key, key).format(*arg))

    def __get__(self, key, *arg, regional=True, **kwargs):# *arg is a trick
        if self.__url__:
            self.__regional__(regional, kwargs)
            return self.__session__.__get__(
                self.__buildUrl__(key, *arg), **kwargs
            )

    def __map_get__(self, key, args, regional=True, **kwargs):
        if self.__url__:
            self.__regional__(regional, kwargs)
            return self.__session__.__map_get__(
                (self.__buildUrl__(key, arg) for arg in args), **kwargs
            )

    # cached -------------------------------------------------------------------

    @cached("videos")
    def __video__(self, videoId):
        return IVVideo(self.__get__("video", videoId))

    @cached("channels")
    def __channel__(self, channelId):
        return IVChannel(self.__get__("channel", channelId))

    def __get_playlist__(self, playlistId, **kwargs):
        return self.__get__("playlist", playlistId, regional=False, **kwargs)

    @cached("playlists")
    def __playlist__(self, playlistId, **kwargs):
        return IVPlaylist(self.__get_playlist__(playlistId, **kwargs))

    # video --------------------------------------------------------------------

    def __fixUrl__(self, video):
        if video and (url := video.get("url")):
            split = urlsplit(url)
            query = split.query.split("&") if split.query else []
            if video["manifestType"] == "mpd" and self.__proxy__:
                query.append("local=true")
            video["url"] = urlunsplit(
                (
                    split.scheme or self.__scheme__,
                    split.netloc or self.__netloc__,
                    split.path,
                    "&".join(query),
                    split.fragment
                )
            )
        return video

    @public
    def video(self, **kwargs):
        if (videoId := kwargs.pop("videoId", None)):
            if kwargs:
                return self.__ytdlp__.video(videoId, **kwargs)
            return self.__fixUrl__(self.__video__(videoId))
        self.logger.error(f"Invalid videoId: {videoId}", notify=True)

    # channel ------------------------------------------------------------------

    def channel(self, **kwargs):
        if (channelId := kwargs.pop("channelId", None)):
            return self.__channel__(channelId)
        self.logger.error(f"Invalid channelId: {channelId}", notify=True)

    @public
    def tabs(self, **kwargs):
        if (channelId := kwargs.pop("channelId", None)):
            return self.__channel__(channelId)["tabs"]
        self.logger.error(f"Invalid channelId: {channelId}", notify=True)

    def __tab__(self, channelId, key, **kwargs):
        #if (("continuation" in kwargs) and (not kwargs["continuation"])):
        #    del kwargs["continuation"]
        if (continuation := kwargs.pop("continuation", None)):
            kwargs["continuation"] = continuation
        return (
            self.__get__(key, channelId, **kwargs),
            self.__channel__(channelId)["channel"]
        )

    @public
    def tab(self, key, **kwargs):
        if (channelId := kwargs.pop("channelId", None)):
            items, channel = self.__tab__(channelId, key, **kwargs)
            return (
                IVVideos(items["videos"]),
                (
                    {"continuation": continuation}
                    if (continuation := items.get("continuation")) else None
                ),
                channel
            )
        self.logger.error(f"Invalid channelId: {channelId}", notify=True)

    @public
    def playlists(self, **kwargs):
        if (channelId := kwargs.pop("channelId", None)):
            items, channel = self.__tab__(channelId, "playlists", **kwargs)
            return (
                IVPlaylists(items["playlists"]),
                (
                    {"continuation": continuation}
                    if (continuation := items.get("continuation")) else None
                ),
                channel
            )
        self.logger.error(f"Invalid channelId: {channelId}", notify=True)

    # playlist -----------------------------------------------------------------

    @public
    def playlist(self, limit=200, **kwargs):
        if (playlistId := kwargs.pop("playlistId", None)):
            items = (
                (item := self.__get_playlist__(playlistId, **kwargs))["videos"]
            )
            return (
                IVVideos(items),
                (
                    {"index": (kwargs["index"] + count)}
                    if ((count := len(items)) >= limit) else None
                ),
                item["title"]
            )
        self.logger.error(f"Invalid playlistId: {playlistId}", notify=True)

    # feed ---------------------------------------------------------------------

    def __feeds__(self, keys):
        cache = self.__cache__.setdefault("channels", {})
        for channel in self.__map_get__("channel", keys):
            if channel:
                videos = channel.pop("latestVideos", [])[:15]
                cache[channel["authorId"]] = IVChannel(channel)
                yield from (IVVideo(video) for video in videos if video)

    def __channels__(self, keys):
        return (self.__channel__(key) for key in keys)

    # --------------------------------------------------------------------------

    def __videos__(self, *args, **kwargs):
        if (videos := self.__get__(*args, **kwargs)):
            return IVVideos(videos)

    @public
    def popular(self, **kwargs):
        return self.__videos__("popular", regional=False, **kwargs)

    @public
    def trending(self, **kwargs):
        return self.__videos__("trending", **kwargs)

    # search -------------------------------------------------------------------

    def search(self, query):
        if (results := self.__get__("search", **query)):
            return IVResults(results)
        return []
