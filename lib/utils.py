# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


from os.path import join

from six import text_type, iteritems
from six.moves.urllib.parse import parse_qsl, urlencode
from kodi_six import xbmc, xbmcaddon, xbmcgui, xbmcvfs


_addon_ = xbmcaddon.Addon()
_addon_id_ = _addon_.getAddonInfo("id")
_addon_name_ = _addon_.getAddonInfo("name")
_addon_path_ = xbmc.translatePath(_addon_.getAddonInfo("path"))
_addon_icon_ = xbmc.translatePath(_addon_.getAddonInfo("icon"))
_addon_profile_ = xbmc.translatePath(_addon_.getAddonInfo("profile"))

_dialog_ = xbmcgui.Dialog()


def getWindowId():
    return xbmcgui.getCurrentWindowId()

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


def parseQuery(query):
    if query.startswith("?"):
        query = query[1:]
    return dict(parse_qsl(query))


def buildUrl(*args, **kwargs):
    params = {k: v.encode("utf-8") if isinstance(v, text_type) else v
              for k, v in iteritems(kwargs)}
    return "?".join(("/".join(args), urlencode(params)))


def localizedString(id):
    if id < 30000:
        return xbmc.getLocalizedString(id)
    return xbmcaddon.Addon().getLocalizedString(id)


def getMediaPath(*args):
    return join(_addon_path_, "resources", "media", *args)

def getIcon(name):
    return getMediaPath("{}.png".format(name))

def makeDataDir():
    if not xbmcvfs.exists(_addon_profile_):
        xbmcvfs.mkdirs(_addon_profile_)


# logging ----------------------------------------------------------------------

def log(msg, level=xbmc.LOGNOTICE):
    xbmc.log("[{}] {}".format(_addon_id_, msg), level=level)

def logDebug(msg):
    log(msg, xbmc.LOGDEBUG)

def logWarning(msg):
    log(msg, xbmc.LOGWARNING)

def logError(msg):
    log(msg, xbmc.LOGERROR)


# settings ---------------------------------------------------------------------

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
    _dialog_.notification(heading, message, icon, time)


# select -----------------------------------------------------------------------

def selectDialog(_list, heading=_addon_name_, multi=False, **kwargs):
    if isinstance(heading, int):
        heading = localizedString(heading)
    if multi:
        return _dialog_.multiselect(heading, _list, **kwargs)
    return _dialog_.select(heading, _list, **kwargs)


# input -----------------------------------------------------------------------

def inputDialog(heading=_addon_name_, **kwargs):
    if isinstance(heading, int):
        heading = localizedString(heading)
    return _dialog_.input(heading, **kwargs)


# search -----------------------------------------------------------------------

_search_heading_ = localizedString(30002)

def searchDialog():
    return inputDialog(_search_heading_)


# listitem ---------------------------------------------------------------------

class ListItem(xbmcgui.ListItem):

    def __new__(cls, label, path, **kwargs):
        return super(ListItem, cls).__new__(
            cls, label=label, path=path, iconImage="", thumbnailImage="",
            offscreen=True)

    def __init__(self, label, path, isFolder=False, infos=None,
                 streamInfos=None, contextMenus=None, **art):
        self.setIsFolder(isFolder)
        self.setIsPlayable(not isFolder)
        self.isFolder = isFolder
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

    def setIsPlayable(self, isPlayable):
        self.setProperty("IsPlayable", "true" if isPlayable else "false")

    def asItem(self):
        return self.getPath(), self, self.isFolder


_more_label_ = localizedString(30099)
_more_icon_ = getIcon("more")

def getMoreItem(url, **kwargs):
    return ListItem(
        _more_label_,  buildUrl(url, **kwargs), isFolder=True,
        infos={"video": {"plot": _more_label_}}, icon=_more_icon_)

