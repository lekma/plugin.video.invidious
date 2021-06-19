# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import requests
import time

from six.moves.urllib.parse import urlunsplit, urlsplit, urljoin

from iapc import Service, public

from tools import (
    buildUrl, log, LOGERROR, notify, ICONERROR, makeDataDir, getSetting
)

from invidious.persistence import updateSearchHistory, clearSearchHistory
from invidious.utils import containerRefresh
from invidious.youtube import YouTubeServer


# ------------------------------------------------------------------------------
# Feed
# ------------------------------------------------------------------------------

class Feed(list):

    def __init__(self, limit=60, timeout=600):
        super(Feed, self).__init__()
        self.limit = limit
        self.max = ((limit // 2) - 1)
        self.timeout = timeout
        self.updated = False
        self.last = 0
        self.ids = None

    def invalid(self, ids):
        if ids != self.ids:
            self.ids = ids
            return True
        return ((time.time() - self.last) > self.timeout)

    def clear(self):
        self *= 0

    def update(self, channel):
        self.extend(channel["latestVideos"][:self.max])
        self.updated = True
        self.last = time.time()

    def page(self, page):
        if self.updated:
            self.sort(key=lambda video: video["published"], reverse=True)
            self.updated = False
        return (self[((page - 1) * self.limit):(page * self.limit)], self.limit)


# ------------------------------------------------------------------------------
# Session
# ------------------------------------------------------------------------------

class Session(requests.Session):

    @staticmethod
    def __notify__(result):
        message = None
        if isinstance(result, Exception):
            message = "session: request error [{}]".format(result)
            log(message, LOGERROR)
        elif isinstance(result, dict):
            message = result.pop("error", None)
            if message and result:
                message = None
        if message:
            notify(message, icon=ICONERROR)
            return True
        return False

    def __init__(self, headers=None):
        super(Session, self).__init__()
        if headers:
            self.headers.update(headers)

    def request(self, method, url, timeout=None, **kwargs):
        log("request.url: {}".format(buildUrl(url, **kwargs.get("params", {}))))
        try:
            response = super(Session, self).request(
                method, url, timeout=timeout, **kwargs
            )
        except requests.Timeout as error:
            self.__notify__(error)
        else:
            try:
                response.raise_for_status()
            except Exception as error:
                try:
                    result = response.json()
                except Exception:
                    result = None
                if not self.__notify__(result):
                    raise error
            else:
                result = response.json()
                if not self.__notify__(result):
                    return result


# ------------------------------------------------------------------------------
# InvidiousService
# ------------------------------------------------------------------------------

class InvidiousService(Service):

    __headers__ = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "*"
    }

    __paths__ = {
        "video": "videos/{}",
        "channel": "channels/{}",
        "playlist": "playlists/{}",
        "videos": "channels/{}/videos",
        "playlists": "channels/{}/playlists"
    }

    __instances__ = "https://api.invidious.io/instances.json"

    def __init__(self, *args, **kwargs):
        super(InvidiousService, self).__init__(*args, **kwargs)
        self.__session__ = Session(headers=self.__headers__)
        self.__channels__ = {}
        self.__query__ = {}
        self.__feed__ = Feed()
        makeDataDir()
        updateSearchHistory()

    def serve_forever(self, timeout):
        self.__httpd__ = YouTubeServer(timeout=timeout)
        while not self.waitForAbort(timeout):
            self.__httpd__.handle_request()
        self.__httpd__.server_close()

    def start(self, **kwargs):
        log("starting service...")
        self.__setup__()
        self.serve(**kwargs)
        log("service stopped")

    def onSettingsChanged(self):
        if self.__history__ and not getSetting("search_history", bool):
            update = (
                (self.__query__.get("action") == "search") and
                (len(self.__query__) > 1)
            )
            clearSearchHistory(update=update)
        self.__setup__()
        containerRefresh()

    # --------------------------------------------------------------------------

    def __setup__(self):
        timeout = getSetting("timeout", float)
        if timeout <= 0:
            self.__timeout__ = None
        else:
            self.__timeout__ = (((timeout - (timeout % 3)) + 0.05), timeout)
        self.__region__ = getSetting("youtube.gl", unicode)
        self.__history__ = getSetting("search_history", bool)
        self.__scheme__ = "https" if getSetting("ssl", bool) else "http"
        self.__netloc__ = getSetting("instance", unicode)
        path = "{}/".format(getSetting("path", unicode).strip("/"))
        self.__url__ = urlunsplit(
            (self.__scheme__, self.__netloc__, path, "", "")
        )
        log("service.url: '{}'".format(self.__url__))
        log("service.timeout: {}".format(self.__timeout__))

    def __get__(self, path, regional=True, **kwargs):
        if regional:
            kwargs.setdefault("region", self.__region__)
        return self.__session__.get(
            urljoin(self.__url__, path), timeout=self.__timeout__, params=kwargs
        )

    # public api ---------------------------------------------------------------

    @public
    def instances(self, **kwargs):
        return self.__session__.get(
            self.__instances__, timeout=self.__timeout__, params=kwargs
        )

    @public
    def query(self, key, *args, **kwargs):
        return self.__get__(
            self.__paths__.get(key, key).format(*args), **kwargs
        )

    def __channel__(self, authorId):
        channel = self.query("channel", authorId)
        if channel:
            self.__channels__[authorId] = channel
            return channel

    @public
    def channel(self, authorId):
        try:
            return self.__channels__[authorId]
        except KeyError:
            return self.__channel__(authorId)

    @public
    def pushQuery(self, query):
        self.__query__ = query

    @public
    def feed(self, ids, page=1, **kwargs):
        page = int(page)
        if page == 1 and self.__feed__.invalid(set(ids)):
            self.__feed__.clear()
            for authorId in ids:
                try:
                    self.__feed__.update(
                        self.query("channel", authorId, **kwargs)
                    )
                except Exception:
                    continue
        return self.__feed__.page(page)

    # video --------------------------------------------------------------------

    def fixUrl(self, url, proxy=False):
        split = urlsplit(url)
        query = split.query.split("&") if split.query else []
        if proxy:
            query.append("local=true")
        return urlunsplit(
            (
                split.scheme or self.__scheme__,
                split.netloc or self.__netloc__,
                split.path,
                "&".join(query),
                split.fragment
            )
        )

    @public
    def video(self, videoId, youtube=False, proxy=False, **kwargs):
        video = self.query("video", videoId, regional=False, **kwargs)
        if video:
            hlsUrl = video.get("hlsUrl", "")
            if youtube:
                video["dashUrl"] = self.__httpd__.dashUrl(videoId)
                if hlsUrl:
                    video["hlsUrl"] = self.__httpd__.hlsUrl(videoId)
            else:
                video["dashUrl"] = self.fixUrl(video["dashUrl"], proxy=proxy)
                if hlsUrl:
                    video["hlsUrl"] = self.fixUrl(hlsUrl, proxy=False)
            return video

    # autogenerated ------------------------------------------------------------

    @public
    def autogenerated(self, authorId, **kwargs):
        return [
            self.query("playlist", playlistId, **kwargs)
            for playlistId in self.__httpd__.playlists(authorId)
        ]


# __main__ ---------------------------------------------------------------------

if __name__ == "__main__":
    InvidiousService().start(timeout=0.5)

