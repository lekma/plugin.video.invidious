# -*- coding: utf-8 -*-


__all__ = [
    "getAddonId", "getAddonName", "getAddonVersion",
    "getAddonPath", "getAddonIcon", "getAddonProfile",
    "Logger",
    "getLanguage", "localizedString", "maybeLocalize",
    "getMediaPath", "getMedia", "makeDataDir",
    "openSettings", "getSetting", "setSetting"
]


from os.path import join

import xbmc, xbmcaddon, xbmcvfs


# addon infos ------------------------------------------------------------------

__addon_id__ = xbmcaddon.Addon().getAddonInfo("id")
__addon_name__ = xbmcaddon.Addon().getAddonInfo("name")
__addon_version__ = xbmcaddon.Addon().getAddonInfo("version")
__addon_path__ = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("path"))
__addon_icon__ = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("icon"))
__addon_profile__ = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("profile"))

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

class Logger(object):

    DEBUG=xbmc.LOGDEBUG
    INFO=xbmc.LOGINFO
    WARNING=xbmc.LOGWARNING
    ERROR=xbmc.LOGERROR

    def __init__(self, id="", component=""):
        self.id = id or __addon_id__
        self.component = component
        self.__prefix__ = (
            f"{f'[{self.id}] ' if self.id else ''}"
            f"{f'<{self.component}> ' if self.component else ''}"
        )

    def __log__(self, message, level):
        xbmc.log(f"{self.__prefix__}{message}", level=level)

    def debug(self, message):
        self.__log__(message, self.DEBUG)

    def info(self, message):
        self.__log__(message, self.INFO)

    def warning(self, message):
        self.__log__(message, self.WARNING)

    def error(self, message):
        self.__log__(message, self.ERROR)

    def getLogger(self, component=""):
        if component == self.component:
            return self
        return Logger(self.id, component=component)


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


__media_path__ = join(__addon_path__, "resources", "media")

def getMediaPath(*args):
    return join(__media_path__, *args)


def getMedia(name, ext="png"):
    return getMediaPath(f"{name}.{ext}")


def makeDataDir():
    if not xbmcvfs.exists(__addon_profile__):
        xbmcvfs.mkdirs(__addon_profile__)


# settings ---------------------------------------------------------------------

def openSettings():
    xbmcaddon.Addon().openSettings()


__get_settings__ = {
    bool: "getSettingBool",
    int: "getSettingInt",
    float: "getSettingNumber",
    str: "getSettingString"
}

def getSetting(id, _type_=None):
    if _type_ is not None:
        return getattr(xbmcaddon.Addon(), __get_settings__[_type_])(id)
    return xbmcaddon.Addon().getSetting(id)


__set_settings__ = {
    bool: "setSettingBool",
    int: "setSettingInt",
    float: "setSettingNumber",
    str: "setSettingString"
}

def setSetting(id, value, _type_=None):
    if _type_ is not None:
        return getattr(xbmcaddon.Addon(), __set_settings__[_type_])(id, value)
    return xbmcaddon.Addon().setSetting(id, value)

