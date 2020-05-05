# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


from os.path import join

from six import text_type, iteritems
from six.moves.urllib.parse import parse_qsl, urlencode
from kodi_six import xbmc, xbmcaddon, xbmcgui


_addon_ = xbmcaddon.Addon()
_addon_id_ = _addon_.getAddonInfo("id")
_addon_path_ = xbmc.translatePath(_addon_.getAddonInfo("path"))
_addon_icon_ = xbmc.translatePath(_addon_.getAddonInfo("icon"))

_dialog_ = xbmcgui.Dialog()


def getWindowId():
    return xbmcgui.getCurrentWindowId()

def getAddonId():
    return _addon_id_

def getAddonPath():
    return _addon_path_

def getAddonIcon():
    return _addon_icon_


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
    return _addon_.getLocalizedString(id)


def getMediaPath(*args):
    return join(_addon_path_, "resources", "media", *args)

def getIcon(name):
    return getMediaPath("{}.png".format(name))


# logging ----------------------------------------------------------------------

def log(msg, level=xbmc.LOGNOTICE):
    xbmc.log("[{}] {}".format(_addon_id_, msg), level=level)


def debug(msg):
    log(msg, xbmc.LOGDEBUG)


def warn(msg):
    log(msg, xbmc.LOGWARNING)


def error(msg):
    log(msg, xbmc.LOGERROR)


# settings ---------------------------------------------------------------------

_get_settings_ = {
    bool: _addon_.getSettingBool,
    int: _addon_.getSettingInt,
    float: _addon_.getSettingNumber,
    unicode: _addon_.getSettingString
}

def getSetting(id, _type=None):
    if _type is not None:
        return _type(_get_settings_.get(_type, _addon_.getSetting)(id))
    return _addon_.getSetting(id)


# notify -----------------------------------------------------------------------

iconInfo = xbmcgui.NOTIFICATION_INFO
iconWarning = xbmcgui.NOTIFICATION_WARNING
iconError = xbmcgui.NOTIFICATION_ERROR

_addon_heading_ = localizedString(30000)

def notify(message, heading=_addon_heading_, icon=_addon_icon_, time=2000):
    if isinstance(message, int):
        message = localizedString(message)
    _dialog_.notification(heading, message, icon, time)


# search -----------------------------------------------------------------------

_search_label_ = localizedString(30002)

def searchDialog():
    return _dialog_.input(_search_label_)


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

