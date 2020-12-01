# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


from os.path import join

from six import text_type, iteritems
from six.moves.urllib.parse import parse_qsl, urlencode
from kodi_six import xbmc, xbmcaddon, xbmcgui, xbmcvfs


# addon infos ------------------------------------------------------------------

_addon_id_ = xbmcaddon.Addon().getAddonInfo("id")
_addon_name_ = xbmcaddon.Addon().getAddonInfo("name")
_addon_path_ = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo("path"))
_addon_icon_ = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo("icon"))
_addon_profile_ = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo("profile"))

def getAddonId():
    return _addon_id_

def getAddonName():
    return _addon_name_

def getAddonPath():
    return _addon_path_

def getAddonIcon():
    return _addon_icon_

def getAddonProfile():
    return _addon_profile_


# logging ----------------------------------------------------------------------

def log(message, level=xbmc.LOGNOTICE):
    xbmc.log("[{}] {}".format(_addon_id_, message), level=level)

def logDebug(message):
    log(message, xbmc.LOGDEBUG)

def logWarning(message):
    log(message, xbmc.LOGWARNING)

def logError(message):
    log(message, xbmc.LOGERROR)


# misc utils -------------------------------------------------------------------

def getWindowId():
    return xbmcgui.getCurrentWindowId()


def localizedString(id):
    if id < 30000:
        return xbmc.getLocalizedString(id)
    return xbmcaddon.Addon().getLocalizedString(id)


def getMediaPath(*args):
    return join(_addon_path_, "resources", "media", *args)


def getThumb(name):
    return getMediaPath("{}.png".format(name))


def makeDataDir():
    if not xbmcvfs.exists(_addon_profile_):
        xbmcvfs.mkdirs(_addon_profile_)


def containerRefresh():
    xbmc.executebuiltin("Container.Refresh()")


def openSettings():
    xbmcaddon.Addon().openSettings()


# parseQuery / buildUrl --------------------------------------------------------

_parse_consts_ = {
    "none": None,
    "true": True,
    "false": False
}

def parseValue(value):
    try:
        return _parse_consts_[value.lower()]
    except KeyError:
        return value

def parseQuery(query):
    if query.startswith("?"):
        query = query[1:]
    return {k: parseValue(v) for k, v in parse_qsl(query)}


def buildUrl(*args, **kwargs):
    params = {k: v.encode("utf-8") if isinstance(v, text_type) else v
              for k, v in iteritems(kwargs)}
    return "?".join(("/".join(args), urlencode(params)))


# get/set settings -------------------------------------------------------------

_get_settings_ = {
    bool: "getSettingBool",
    int: "getSettingInt",
    float: "getSettingNumber",
    unicode: "getSettingString"
}

def getSetting(id, _type=None):
    if _type is not None:
        return _type(getattr(xbmcaddon.Addon(), _get_settings_[_type])(id))
    return xbmcaddon.Addon().getSetting(id)


_set_settings_ = {
    bool: "setSettingBool",
    int: "setSettingInt",
    float: "setSettingNumber",
    unicode: "setSettingString"
}

def setSetting(id, value, _type=None):
    if _type is not None:
        return getattr(xbmcaddon.Addon(), _set_settings_[_type])(id, _type(value))
    return xbmcaddon.Addon().setSetting(id, value)


# notify -----------------------------------------------------------------------

iconInfo = xbmcgui.NOTIFICATION_INFO
iconWarning = xbmcgui.NOTIFICATION_WARNING
iconError = xbmcgui.NOTIFICATION_ERROR

def notify(message, heading=_addon_name_, icon=_addon_icon_, time=5000):
    if isinstance(message, int):
        message = localizedString(message)
    if isinstance(heading, int):
        heading = localizedString(heading)
    xbmcgui.Dialog().notification(heading, message, icon, time)


# select -----------------------------------------------------------------------

def selectDialog(_list, heading=_addon_name_, multi=False, **kwargs):
    if isinstance(heading, int):
        heading = localizedString(heading)
    if multi:
        return xbmcgui.Dialog().multiselect(heading, _list, **kwargs)
    return xbmcgui.Dialog().select(heading, _list, **kwargs)


# input -----------------------------------------------------------------------

def inputDialog(heading=_addon_name_, **kwargs):
    if isinstance(heading, int):
        heading = localizedString(heading)
    return xbmcgui.Dialog().input(heading, **kwargs)


# search -----------------------------------------------------------------------

_search_heading_ = localizedString(30002)

def searchDialog():
    return inputDialog(_search_heading_)


# listitem ---------------------------------------------------------------------

class ListItem(xbmcgui.ListItem):

    def __new__(cls, label, path, **kwargs):
        return super(ListItem, cls).__new__(cls, label=label, path=path)

    def __init__(self, label, path, isFolder=False, isPlayable=True,
                 infos=None, streamInfos=None, contextMenus=None, **art):
        self.setIsFolder(isFolder)
        self.setIsPlayable(False if isFolder else isPlayable)
        if infos:
            for info in iteritems(infos):
                self.setInfo(*info)
        if streamInfos:
            for info in iteritems(streamInfos):
                self.addStreamInfo(*info)
        if contextMenus:
            self.addContextMenuItems(contextMenus)
        if art:
            self.setArt(art)

    def setIsFolder(self, isFolder):
        super(ListItem, self).setIsFolder(isFolder)
        #self.setProperty("IsFolder", str(isFolder).lower())
        self.isFolder = isFolder

    def setIsPlayable(self, isPlayable):
        self.setProperty("IsPlayable", str(isPlayable).lower())
        self.isPlayable = isPlayable

    def asItem(self):
        return self.getPath(), self, self.isFolder


# more item --------------------------------------------------------------------

_more_label_ = localizedString(30099)
_more_thumb_ = getThumb("more")

def getMoreItem(url, **kwargs):
    return ListItem(
        _more_label_,  buildUrl(url, **kwargs), isFolder=True,
        infos={"video": {"plot": _more_label_}}, thumb=_more_thumb_)


# settings item ----------------------------------------------------------------

_settings_label_ = localizedString(30100)
_settings_thumb_ = getThumb("settings")

def getSettingsItem(url, **kwargs):
    return ListItem(
        _settings_label_,  buildUrl(url, **kwargs), isPlayable=False,
        infos={"video": {"plot": _settings_label_}}, thumb=_settings_thumb_)

