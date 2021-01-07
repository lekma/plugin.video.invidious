# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


__all__ = [
    "getAddonId", "getAddonName", "getAddonVersion",
    "getAddonPath", "getAddonIcon", "getAddonProfile",
    "LOGDEBUG", "LOGINFO", "LOGWARNING", "LOGERROR", "log",
    "getLanguage", "localizedString", "maybeLocalize",
    "getMediaPath", "getMedia", "makeDataDir",
    "openSettings", "getSetting", "setSetting",
    "executeBuiltin", "JSONRPCError", "executeJSONRPC"
]


from os.path import join
from json import dumps, loads

from kodi_six import xbmc, xbmcaddon, xbmcvfs


# addon infos ------------------------------------------------------------------

__addon_id__ = xbmcaddon.Addon().getAddonInfo("id")
__addon_name__ = xbmcaddon.Addon().getAddonInfo("name")
__addon_version__ = xbmcaddon.Addon().getAddonInfo("version")
__addon_path__ = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo("path"))
__addon_icon__ = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo("icon"))
__addon_profile__ = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo("profile"))

def getAddonId():
    return __addon_id__

def getAddonName():
    return __addon_name__

def getAddonVersion():
    return __addon_version__

def getAddonPath():
    return __addon_path__

def getAddonIcon():
    return __addon_icon__

def getAddonProfile():
    return __addon_profile__


# logging ----------------------------------------------------------------------

LOGDEBUG=xbmc.LOGDEBUG
LOGINFO=xbmc.LOGINFO
LOGWARNING=xbmc.LOGWARNING
LOGERROR=xbmc.LOGERROR

def log(message, level=LOGINFO):
    xbmc.log("[{}] {}".format(__addon_id__, message), level=level)


# misc utils -------------------------------------------------------------------

def getLanguage():
    return xbmc.getLanguage(xbmc.ISO_639_1) or "en"


def localizedString(id):
    if id < 30000:
        return xbmc.getLocalizedString(id)
    return xbmcaddon.Addon().getLocalizedString(id)


def maybeLocalize(value):
    if isinstance(value, int):
        return localizedString(value)
    return value


def getMediaPath(*args):
    return join(__addon_path__, "resources", "media", *args)


def getMedia(name, ext="png"):
    return getMediaPath("{}.{}".format(name, ext))


def makeDataDir():
    if not xbmcvfs.exists(__addon_profile__):
        xbmcvfs.mkdirs(__addon_profile__)


def openSettings():
    xbmcaddon.Addon().openSettings()


# get/set settings -------------------------------------------------------------

__get_settings__ = {
    bool: "getSettingBool",
    int: "getSettingInt",
    float: "getSettingNumber",
    unicode: "getSettingString"
}

def getSetting(id, _type=None):
    if _type is not None:
        return _type(getattr(xbmcaddon.Addon(), __get_settings__[_type])(id))
    return xbmcaddon.Addon().getSetting(id)


__set_settings__ = {
    bool: "setSettingBool",
    int: "setSettingInt",
    float: "setSettingNumber",
    unicode: "setSettingString"
}

def setSetting(id, value, _type=None):
    if _type is not None:
        return getattr(xbmcaddon.Addon(), __set_settings__[_type])(
            id, _type(value)
        )
    return xbmcaddon.Addon().setSetting(id, value)


# executebuiltin ---------------------------------------------------------------

def executeBuiltin(function, *args):
    xbmc.executebuiltin("{}({})".format(function, ",".join(args)))


# executeJSONRPC ---------------------------------------------------------------

class JSONRPCError(Exception):

    __error_msg__ = "[{code}] {message}"
    __data_msg__ = "in {method}."
    __stack_msg__ = "{message} ({name})"

    def __init__(self, error):
        message = self.__error_msg__.format(**error)
        data = error.get("data")
        if data:
            message = " ".join((message, self.data(data)))
        super(JSONRPCError, self).__init__(message)

    def data(self, data):
        message = self.__data_msg__.format(**data)
        try:
            # unfortunately kodi doesn't respect its own specification :(
            try:
                _message_ = data["message"]
            except KeyError:
                _message_ = self.stack(data["stack"])
            message = " ".join((_message_, message))
        except KeyError:
            pass
        return message

    def stack(self, stack):
        return self.__stack_msg__.format(**stack)


__jsonrpc_request__ = {
    "id": 1,
    "jsonrpc": "2.0",
}

def executeJSONRPC(method, **kwargs):
    request = dict(__jsonrpc_request__, method=method, params=kwargs)
    error = loads(xbmc.executeJSONRPC(dumps(request))).get("error")
    if error:
        raise JSONRPCError(error)
