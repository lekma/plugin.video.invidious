# -*- coding: utf-8 -*-


from requests import Session, Timeout
from time import time
from urllib.parse import urlunsplit, urlsplit, urljoin

from iapc import Service, public
from iapc.tools import (
    makeProfile, containerRefresh, buildUrl, notify, ICONERROR, getSetting
)

from invidious.search import clearSearchHistory
from invidious.youtube import YouTubeServer


# ------------------------------------------------------------------------------
# InvidiousFeed

class InvidiousFeed(list):

    def __init__(self, limit=60, timeout=600):
        super(InvidiousFeed, self).__init__()
        self.limit = limit
        self.max = ((limit // 4) - 1)
        self.timeout = timeout
        self.updated = False
        self.last = 0
        self.ids = None

    def invalid(self, ids):
        if ids != self.ids:
            self.ids = ids
            return True
        return ((time() - self.last) > self.timeout)

    def update(self, channel):
        self.extend(channel["latestVideos"][:self.max])
        self.updated = True
        self.last = time()

    def page(self, page):
        if self.updated:
            self.sort(key=lambda video: video["published"], reverse=True)
            self.updated = False
        return (self[((page - 1) * self.limit):(page * self.limit)], self.limit)

# ------------------------------------------------------------------------------
# InvidiousSession

class InvidiousSession(Session):

    def __init__(self, logger):
        super(InvidiousSession, self).__init__()
        self.logger = logger.getLogger("service.session")
        self.__setup__(True)

    def __setup__(self, init=False, headers=None):
        if headers:
            self.headers.update(headers)
        if (timeout := getSetting("timeout", float)) <= 0.0:
            self.timeout = None
        else:
            self.timeout = (((timeout - (timeout % 3)) + 0.05), timeout)
        if not init:
            self.logger.info(f"timeout: {self.timeout}")

    def __notify__(self, result):
        message = None
        if isinstance(result, Exception):
            message = f"request error [{result}]"
            self.logger.error(message)
        elif isinstance(result, dict):
            message = result.pop("error", None)
            if message and result:
                message = None
        if message:
            notify(message, icon=ICONERROR)
            return True
        return False

    def request(self, method, url, **kwargs):
        self.logger.info(f"request: {buildUrl(url, **kwargs.get('params', {}))}")
        try:
            response = super(InvidiousSession, self).request(
                method, url, timeout=self.timeout, **kwargs
            )
        except Timeout as error:
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
        self.__session__ = InvidiousSession(self.logger)
        self.__channels__ = {}
        self.__query__ = {}
        self.__feed__ = InvidiousFeed()
        makeProfile()

    def serve_forever(self, timeout):
        self.__httpd__ = YouTubeServer(self.id, timeout=timeout)
        while not self.waitForAbort(timeout):
            self.__httpd__.handle_request()
        self.__httpd__.server_close()

    def start(self, **kwargs):
        self.logger.info("starting...")
        self.__setup__()
        self.serve(**kwargs)
        self.logger.info("stopped")

    def onSettingsChanged(self):
        if self.__history__ and not getSetting("history", bool):
            update = (
                (self.__query__.get("action") == "search") and
                (len(self.__query__) > 1)
            )
            clearSearchHistory(update=update)
        self.__setup__()
        containerRefresh()

    # --------------------------------------------------------------------------

    def __setup__(self):
        self.__region__ = getSetting("gl", str)
        self.__history__ = getSetting("history", bool)
        self.__scheme__ = "https" if getSetting("ssl", bool) else "http"
        self.__netloc__ = getSetting("instance", str)
        path = f"{getSetting('path', str).strip('/')}/"
        self.__url__ = urlunsplit(
            (self.__scheme__, self.__netloc__, path, "", "")
        )

        token = getSetting("token", str)
        if token:
            self.__headers__["Authorization"] = f"Bearer {token}"
        else:
            self.__headers__.pop("Authorization", None)

        self.logger.info(f"instance: {self.__url__!r}")
        self.__session__.__setup__(headers=self.__headers__)

    def __get__(self, path, regional=True, **kwargs):
        if regional:
            kwargs.setdefault("region", self.__region__)
        return self.__session__.get(urljoin(self.__url__, path), params=kwargs)

    # public api ---------------------------------------------------------------

    @public
    def instances(self, **kwargs):
        return self.__session__.get(self.__instances__, params=kwargs)

    @public
    def query(self, key, *args, **kwargs):
        return self.__get__(
            self.__paths__.get(key, key).format(*args), **kwargs
        )

    def __channel__(self, authorId):
        if (channel := self.query("channel", authorId)):
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
        if ((page := int(page)) == 1) and self.__feed__.invalid(set(ids)):
            self.__feed__.clear()
            for authorId in ids:
                try:
                    self.__feed__.update(
                        self.query("channel", authorId, **kwargs)
                    )
                except Exception:
                    continue
        return self.__feed__.page(page)

    @public
    def isLoggedIn(self):
        return self.__headers__.__contains__("Authorization")

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
        if (video := self.query("video", videoId, regional=False, **kwargs)):
            headers = {}
            hlsUrl = video.get("hlsUrl", "")
            if youtube:
                video["dashUrl"] = self.__httpd__.dashUrl(videoId)
                if hlsUrl:
                    video["hlsUrl"] = self.__httpd__.hlsUrl(videoId)
            else:
                headers = self.__headers__
                video["dashUrl"] = self.fixUrl(video["dashUrl"], proxy=proxy)
                if hlsUrl:
                    video["hlsUrl"] = self.fixUrl(hlsUrl, proxy=False)
            return (video, headers)
        return (None, None)

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
