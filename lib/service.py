# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import requests

from six.moves.urllib.parse import urljoin, urlunsplit

import objects
from iac import Service, public
from utils import getSetting, notify, log, error, iconError


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
                error("session: error processing request [{}]".format(msg))
                return notify(msg, icon=iconError, time=5000)
            raise err
        else:
            return response.json()


# ------------------------------------------------------------------------------
# Service
# ------------------------------------------------------------------------------

class Fields(dict):

    def __init__(self, default=None, **kwargs):
        if default:
            self.update(default=default.fields())
        self.update(((k, v.fields()) for k, v in kwargs.items()))

    def __missing__(self, key):
        if "default" in self:
            return self["default"]
        raise KeyError(key)


class InvidiousService(Service):

    _headers_ = {}

    # XXX: this is really clunky, needs a better approach
    _requests_ = {
        "top": ("top", Fields(objects.StdVideos)),
        "popular": ("popular", Fields(objects.ShortVideos)),
        "trending": ("trending", Fields(objects.Videos)),
        "videos": ("channels/{}/videos", Fields(objects.Videos)),
        "channel": ("channels/{}", Fields(objects.Channel)),
        "video": ("videos/{}", Fields(objects.Video)),
        "playlists": ("channels/{}/playlists", Fields(objects.ChannelPlaylists)),
        "playlist": ("playlists/{}", Fields(objects.Playlist)),
        "search": (
            "search",
            Fields(
                video=objects.Videos,
                channel=objects.Channels,
                playlist=objects.Playlists
            )
        )
    }

    def __init__(self, *args, **kwargs):
        super(InvidiousService, self).__init__(*args, **kwargs)
        self.session = InvidiousSession(headers=self._headers_)
        self.channels = {}

    def setup(self):
        self.scheme = "https" if getSetting("ssl", bool) else "http"
        self.netloc = getSetting("instance", unicode)
        path = "{}/".format(getSetting("path", unicode).strip("/"))
        self.url = urlunsplit((self.scheme, self.netloc, path, "", ""))
        self.use_fields = getSetting("fields", bool)
        log("service.url: '{}'".format(self.url))
        log("service.use_fields: {}".format(self.use_fields))

    def start(self):
        log("starting service...")
        self.setup()
        self.serve()
        log("service stopped")

    def onSettingsChanged(self):
        self.setup()

    def get(self, url, **kwargs):
        return self.session.get(urljoin(self.url, url), params=kwargs)

    # public api ---------------------------------------------------------------

    @public
    def query(self, key, *args, **kwargs):
        url, fields = self._requests_[key]
        if self.use_fields:
            fields = fields[kwargs.get("type", "default")]
            if fields:
                kwargs["fields"] = ",".join(fields)
        return self.get(url.format(*args), **kwargs)

    def _get_channel(self, authorId):
        channel = self.query("channel", authorId)
        if channel:
            self.channels[authorId] = channel
            return channel

    @public
    def channel_(self, authorId):
        try:
            return self.channels[authorId]
        except KeyError:
            return self._get_channel(authorId)

    @public
    def scheme_(self):
        return self.scheme

    @public
    def netloc_(self):
        return self.netloc


# __main__ ---------------------------------------------------------------------

if __name__ == "__main__":

    InvidiousService().start()

