# -*- coding: utf-8 -*-


from collections import OrderedDict
from json import JSONDecoder
from requests import get, Timeout
from time import time
from urllib.parse import parse_qs

from iapc import Server, http

from tools import buildUrl, getSetting, notify, ICONERROR

from .find import PatternsError, __find__, findInValues
from .playlists import adaptive
from .js import Solver


# find -------------------------------------------------------------------------

def find(html, *patterns):
    for pattern in patterns:
        try:
            return JSONDecoder(strict=False).raw_decode(
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
# YouTubeSession

class YouTubeSession(object):

    __headers__ = {}
    __baseUrl__ = "https://www.youtube.com"

    def __init__(self, logger, headers=None):
        self.logger = logger.getLogger("youtube")
        if headers:
            self.headers.update(headers)

    def __get__(self, url, **kwargs):
        self.logger.info(
            f"request: {buildUrl(url, **kwargs.get('params', {}))}"
        )
        try:
            response = get(
                url, headers=self.__headers__, timeout=(60.05, 60.0), **kwargs
            )
        except Timeout as error:
            self.logger.error(message := f"error: {error}")
            notify(message, icon=ICONERROR)
        else:
            response.raise_for_status()
            return response.text

    def js(self, jsUrl):
        return self.__get__(f"{self.__baseUrl__}{jsUrl}")

    def video(self, videoId):
        params = {"v": videoId, "hl": getSetting("hl", str)}
        return self.__get__(f"{self.__baseUrl__}/watch", params=params)

    def playlists(self, authorId):
        params = {
            "view": "1",
            "sort": "lad",
            "hl": getSetting("hl", str),
            "gl": getSetting("gl", str)
        }
        return self.__get__(
            f"{self.__baseUrl__}/channel/{authorId}/playlists", params=params
        )


# ------------------------------------------------------------------------------
# YouTubeServer

class YouTubeServer(Server):

    def __init__(self, id, timeout=-1, headers=None):
        super().__init__(id, timeout=timeout)
        self.__manifestUrl__ = "http://{}:{}/manifest?videoId={{}}".format(
            *self.server_address
        )
        self.__session__ = YouTubeSession(self.logger, headers=headers)
        self.__solvers__ = {}

    def __raise__(self, error):
        if not isinstance(error, Exception):
            error = Exception(error)
        notify(f"{error}", icon=ICONERROR)
        raise error

    # --------------------------------------------------------------------------

    def __solver__(self, jsUrl):
        solver = Solver(self.__session__.js(jsUrl))
        self.__solvers__[jsUrl] = solver
        return solver

    def solver(self, jsUrl):
        try:
            solver = self.__solvers__[jsUrl]
            if time() >= solver.__expire__:
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
        if (isLive := videoDetails.get("isLive", False)):
            if (hlsUrl := streamingData.get("hlsManifestUrl", "")):
                # Content-Type: application/vnd.apple.mpegurl
                return (302, None, {"Location": hlsUrl})
        elif (streams := streamingData.get("adaptiveFormats", [])):
            jsUrl = videoDetails["jsUrl"]
            for stream in streams:
                if "url" not in stream:
                    stream["url"] = self.extractUrl(stream, jsUrl)
            # Content-Type: video/vnd.mpeg.dash.mpd
            return (200, adaptive(videoDetails["lengthSeconds"], streams), None)
        self.__raise__(f"Cannot play video: '{videoId}'")

