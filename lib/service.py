# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import requests

from six.moves.urllib.parse import urljoin, urlunsplit

import objects
from iapc import Service, public
from utils import getSetting, notify, log, logError, iconError


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

class InvidiousService(Service):

    _headers_ = {}

    _urls_ = {
        "videos": "channels/{}/videos",
        "channel": "channels/{}",
        "video": "videos/{}",
        "playlists": "channels/{}/playlists",
        "playlist": "playlists/{}"
    }

    def __init__(self, *args, **kwargs):
        super(InvidiousService, self).__init__(*args, **kwargs)
        self.session = InvidiousSession(headers=self._headers_)
        self.channels = {}

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
        return self.session.get(urljoin(self._url, url), params=kwargs)

    # public api ---------------------------------------------------------------

    @public
    def query(self, key, *args, **kwargs):
        return self.get(self._urls_.get(key, key).format(*args), **kwargs)

    def _get_channel(self, authorId):
        channel = self.query("channel", authorId)
        if channel:
            self.channels[authorId] = channel
            return channel

    @public
    def channel(self, authorId):
        try:
            return self.channels[authorId]
        except KeyError:
            return self._get_channel(authorId)

    @public
    def scheme(self):
        return self._scheme

    @public
    def netloc(self):
        return self._netloc


# __main__ ---------------------------------------------------------------------

if __name__ == "__main__":

    InvidiousService().start()

