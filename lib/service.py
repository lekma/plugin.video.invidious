# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import requests
import time

from six.moves.urllib.parse import urljoin, urlunsplit

from iapc import Service, public
from utils import getSetting, notify, log, logError, iconError, makeDataDir


# ------------------------------------------------------------------------------
# Session
# ------------------------------------------------------------------------------

class InvidiousSession(requests.Session):

    def __init__(self, headers=None):
        super(InvidiousSession, self).__init__()
        if headers:
            self.headers.update(headers)

    def request(self, *args, **kwargs):
        response = super(InvidiousSession, self).request(*args, **kwargs)
        log("request.url: {}".format(response.url))
        try:
            response.raise_for_status()
        except Exception as err:
            try:
                msg = response.json().get("error")
            except Exception:
                msg = None
            if msg:
                logError("session: error processing request [{}]".format(msg))
                return notify(msg, icon=iconError)
            raise err
        else:
            return response.json()


# ------------------------------------------------------------------------------
# Service
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


class InvidiousService(Service):

    _headers_ = {}

    _urls_ = {
        "videos": "channels/{}/videos",
        "channel": "channels/{}",
        "video": "videos/{}",
        "playlists": "channels/{}/playlists",
        "playlist": "playlists/{}"
    }

    _instances_url_ = "https://instances.invidio.us/instances.json"

    def __init__(self, *args, **kwargs):
        super(InvidiousService, self).__init__(*args, **kwargs)
        self._session_ = InvidiousSession(headers=self._headers_)
        self._channels_ = {}
        self._feed_ = Feed()
        makeDataDir()

    def setup(self):
        self._scheme = "https" if getSetting("ssl", bool) else "http"
        self._netloc = getSetting("instance", unicode)
        _path = "{}/".format(getSetting("path", unicode).strip("/"))
        self._url = urlunsplit((self._scheme, self._netloc, _path, "", ""))
        log("service.url: '{}'".format(self._url))

    def start(self):
        log("starting service...")
        self.setup()
        self.serve()
        log("service stopped")

    def onSettingsChanged(self):
        self.setup()

    def get(self, url, **kwargs):
        return self._session_.get(urljoin(self._url, url), params=kwargs)

    # public api ---------------------------------------------------------------

    @public
    def query(self, key, *args, **kwargs):
        return self.get(self._urls_.get(key, key).format(*args), **kwargs)

    def _get_channel(self, authorId):
        channel = self.query("channel", authorId)
        if channel:
            self._channels_[authorId] = channel
            return channel

    @public
    def channel(self, authorId):
        try:
            return self._channels_[authorId]
        except KeyError:
            return self._get_channel(authorId)

    @public
    def scheme(self):
        return self._scheme

    @public
    def netloc(self):
        return self._netloc

    @public
    def instances(self, **kwargs):
        return self._session_.get(self._instances_url_, params=kwargs)

    @public
    def feed(self, ids, page=1, **kwargs):
        page = int(page)
        if page == 1 and self._feed_.invalid(set(ids)):
            self._feed_.clear()
            for authorId in ids:
                try:
                    self._feed_.update(self.query("channel", authorId))
                except Exception:
                    continue
        return self._feed_.page(page)


# __main__ ---------------------------------------------------------------------

if __name__ == "__main__":

    InvidiousService().start()

