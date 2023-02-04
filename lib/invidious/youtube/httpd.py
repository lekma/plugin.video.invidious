# -*- coding: utf-8 -*-


from collections import OrderedDict
from json import JSONDecoder
from random import randint
from requests import Session, Timeout
from time import time

from iapc import Server, http
from iapc.tools import buildUrl, getSetting, notify, ICONERROR

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
# HttpSession

class HttpSession(Session):

    __timeout__ = (60.05, 60.0)

    def __init__(self, logger, name, headers=None):
        super(HttpSession, self).__init__()
        self.logger = logger.getLogger(name)
        if headers:
            self.headers.update(headers)

    def request(self, method, url, **kwargs):
        self.logger.info(f"request: {buildUrl(url, **kwargs.get('params', {}))}")
        try:
            response = super(HttpSession, self).request(
                method, url, timeout=self.__timeout__, **kwargs
            )
        except Timeout as error:
            self.logger.error(message := f"error: {error}")
            notify(message, icon=ICONERROR)
        else:
            response.raise_for_status()
            return response


# ------------------------------------------------------------------------------
# YouTubeSession

class YouTubeSession(HttpSession):

    __url__ = "https://www.youtube.com"

    def request(self, *args, **kwargs):
        return super(YouTubeSession, self).request(*args, **kwargs).text

    def get(self, url, **kwargs):
        if (
            (not (consent := self.cookies.get("CONSENT"))) or
            ("YES" not in consent)
        ):
            html = super(YouTubeSession, self).get(self.__url__)
            try:
                value = __find__(r'cb\..+?(?=\")', html).group()
            except PatternsError:
                if (
                    (consent := self.cookies.get("CONSENT")) and
                    ("PENDING" in consent)
                ):
                    cid = consent.split("+")[1]
                else:
                    cid = randint(100, 999)
                value = f"cb.20221213-07-p1.en+FX+{cid}"
            self.cookies.set("CONSENT", f"YES+{value}", domain=".youtube.com")
        return super(YouTubeSession, self).get(url, **kwargs)

    def js(self, jsUrl):
        return self.get(f"{self.__url__}{jsUrl}")

    def video(self, videoId):
        params = {"v": videoId, "hl": getSetting("hl", str)}
        return self.get(f"{self.__url__}/watch", params=params)

    def playlists(self, authorId):
        params = {
            "view": "1",
            "sort": "lad",
            "hl": getSetting("hl", str),
            "gl": getSetting("gl", str)
        }
        return self.get(
            f"{self.__url__}/channel/{authorId}/playlists", params=params
        )


# ------------------------------------------------------------------------------
# YouTubeServer

class YouTubeServer(Server):

    def __init__(self, id, timeout=-1, headers=None):
        super(YouTubeServer, self).__init__(id, timeout=timeout)
        self.__manifestUrl__ = "http://{}:{}/manifest?videoId={{}}".format(
            *self.server_address
        )
        self.__session__ = YouTubeSession(self.logger, "youtube", headers=headers)
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
        jsUrl = find(
            html,
            r"PLAYER_JS_URL\s*['\"]\s*:[^'\"]*",
            r"jsUrl\s*['\"]\s*:[^'\"]*"
        )
        status = video["playabilityStatus"]
        if status["status"].lower() == "ok":
            video["videoDetails"]["jsUrl"] = jsUrl
            return video
        self.__raise__(status.get("reason", "Unknown error"))

    # --------------------------------------------------------------------------

    def playlists(self, authorId):
        return findPlaylists(
            find(self.__session__.playlists(authorId), r"ytInitialData\s*=\s*")
        )

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
            solver = self.solver(videoDetails["jsUrl"])
            for stream in streams:
                stream["url"] = solver.extractUrl(stream)
            # Content-Type: video/vnd.mpeg.dash.mpd
            return (200, adaptive(videoDetails["lengthSeconds"], streams), None)
        self.__raise__(f"Cannot play video: '{videoId}'")
