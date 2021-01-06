# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import requests
import re
import json
import time

from collections import OrderedDict

from six.moves.urllib.parse import parse_qs

from iapc import Server, http

from tools import buildUrl, getSetting, notify, ICONERROR, log

from .find import PatternsError, __find__, findInValues
from .playlists import adaptive
from .js import Solver


# ------------------------------------------------------------------------------
# find
# ------------------------------------------------------------------------------

def find(html, *patterns):
    for pattern in patterns:
        try:
            return json.JSONDecoder(strict=False).raw_decode(
                html[__find__(pattern, html).end():]
            )[0]
        except (PatternsError, ValueError):
            continue
    raise PatternsError(*patterns)


def findPlaylists(data):
    result = OrderedDict()
    findInValues(data.values(), "/playlist?list=", result.setdefault)
    return [playlist.split("=")[1] for playlist in result.keys()]


# ------------------------------------------------------------------------------
# Session
# ------------------------------------------------------------------------------

class Session(object):

    __headers__ = {}
    __baseUrl__ = "https://www.youtube.com"

    def __init__(self, headers=None):
        if headers:
            self.__headers__.update(headers)

    def get(self, url, **kwargs):
        log("youtube.url: {}".format(buildUrl(url, **kwargs.get("params", {}))))
        try:
            response = requests.get(
                url, headers=self.__headers__, timeout=(9.05, 30.0), **kwargs
            )
        except requests.Timeout as error:
            message = "youtube: {}".format(error)
            log(message, LOGERROR)
            notify(message, icon=ICONERROR)
        else:
            response.raise_for_status()
            return response.text

    def js(self, jsUrl):
        return self.get("".join((self.__baseUrl__, jsUrl)))

    def video(self, videoId):
        params = {"v": videoId, "hl": getSetting("youtube.hl", unicode)}
        return self.get("".join((self.__baseUrl__, "/watch")), params=params)

    def playlists(self, authorId):
        params = {
            "view": "1",
            "sort": "lad",
            "hl": getSetting("youtube.hl", unicode),
            "gl": getSetting("youtube.gl", unicode)
        }
        return self.get(
            "".join((self.__baseUrl__, "/channel/{}/playlists".format(authorId))),
            params=params
        )


# ------------------------------------------------------------------------------
# YouTubeServer
# ------------------------------------------------------------------------------

class YouTubeServer(Server):

    def __init__(self, headers=None, timeout=1):
        Server.__init__(self, timeout=timeout)
        self.__manifestUrl__ = "http://{}:{}/manifest?videoId={{}}".format(
            *self.server_address
        )
        self.__session__ = Session(headers=headers)
        self.__solvers__ = {}

    def __raise__(self, error):
        if not isinstance(error, Exception):
            error = Exception(error)
        notify("{}".format(error), icon=ICONERROR)
        raise error

    # --------------------------------------------------------------------------

    def __solver__(self, jsUrl):
        solver = Solver(self.__session__.js(jsUrl))
        self.__solvers__[jsUrl] = solver
        return solver

    def solver(self, jsUrl):
        try:
            solver = self.__solvers__[jsUrl]
            if time.time() >= solver.__expire__:
                solver = self.__solver__(jsUrl)
            return solver
        except KeyError:
            return self.__solver__(jsUrl)

    # --------------------------------------------------------------------------

    def video(self, videoId):
        html = self.__session__.video(videoId)
        video = find(html, r"ytInitialPlayerResponse\s*=\s*")
        status = video["playabilityStatus"]
        if status["status"].lower() == "ok":
            config = find(html, r"ytplayer.web_player_context_config\s*=\s*")
            video["videoDetails"]["jsUrl"] = config["jsUrl"]
            return video
        self.__raise__(status.get("reason", "Unknown error"))

    # --------------------------------------------------------------------------

    def playlists(self, authorId):
        return findPlaylists(
            find(self.__session__.playlists(authorId), r"ytInitialData\s*=\s*")
        )

    # --------------------------------------------------------------------------

    def extractUrl(self, stream, jsUrl):
        try:
            cipher = stream["cipher"]
        except KeyError:
            cipher = stream["signatureCipher"]
        return self.solver(jsUrl).extractUrl(parse_qs(cipher))

    # --------------------------------------------------------------------------

    def dashUrl(self, videoId):
        return self.__manifestUrl__.format(videoId)

    def hlsUrl(self, videoId):
        return self.video(videoId)["streamingData"]["hlsManifestUrl"]

    # http ---------------------------------------------------------------------

    @http()
    def manifest(self, **kwargs):
        videoId = kwargs["videoId"]
        video = self.video(videoId)
        streamingData = video["streamingData"]
        videoDetails = video["videoDetails"]
        isLive = videoDetails.get("isLive", False)
        if isLive:
            #Content-Type: application/vnd.apple.mpegurl
            hlsUrl = streamingData.get("hlsManifestUrl", "")
            if hlsUrl:
                return (302, None, {"Location": hlsUrl})
        else:
            #Content-Type: video/vnd.mpeg.dash.mpd
            streams = streamingData.get("adaptiveFormats", [])
            if streams:
                jsUrl = videoDetails["jsUrl"]
                for stream in streams:
                    if "url" not in stream:
                        stream["url"] = self.extractUrl(stream, jsUrl)
                duration = videoDetails["lengthSeconds"]
                return (200, adaptive(duration, streams), None)
        self.__raise__("Cannot play video: '{0}'".format(videoId))

