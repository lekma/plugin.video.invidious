# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


from os.path import join

from six import text_type, iteritems
from six.moves.urllib.parse import parse_qsl, urlencode
from kodi_six import xbmc, xbmcaddon, xbmcgui


addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo("path"))
addonId = xbmc.translatePath(addon.getAddonInfo("id"))

dialog = xbmcgui.Dialog()


def parse_query(query):
    if query.startswith("?"):
        query = query[1:]
    return dict(parse_qsl(query))


def build_url(*args, **kwargs):
    params = {k: v.encode("utf-8") if isinstance(v, text_type) else v
              for k, v in iteritems(kwargs)}
    return "?".join(("/".join(args), urlencode(params)))


def localized_string(id):
    if id < 30000:
        return xbmc.getLocalizedString(id)
    return addon.getLocalizedString(id)


def get_media_path(*args):
    return join(addonPath, "resources", "media", *args)

def get_icon(name):
    return get_media_path("{}.png".format(name))


# settings ---------------------------------------------------------------------

_get_settings_ = {
    bool: "getSettingBool",
    int: "getSettingInt",
    float: "getSettingNumber",
    unicode: "getSettingString"
}

def get_setting(id, _type=None):
    if _type is not None:
        return _type(getattr(addon, _get_settings_.get(_type, "getSetting"))(id))
    return addon.getSetting(id)


# logging ----------------------------------------------------------------------

def log(msg, level=xbmc.LOGNOTICE):
    xbmc.log("{}: {}".format(addon.getAddonInfo("id"), msg), level=level)


def debug(msg):
    log(msg, xbmc.LOGDEBUG)


def warn(msg):
    log(msg, xbmc.LOGWARNING)


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
            self. addContextMenuItems(contextMenus)
        if art:
            self.setArt(art)

    def setIsPlayable(self, isPlayable):
        self.setProperty("IsPlayable", "true" if isPlayable else "false")

    def asItem(self):
        return self.getPath(), self, self.isFolder


_more_label_ = localized_string(30099)
_more_icon_ = get_icon("more")

def more_item(url, **kwargs):
    return ListItem(
        _more_label_,  build_url(url, **kwargs), isFolder=True,
        infos={"video": {"plot": _more_label_}}, icon=_more_icon_)


# search -----------------------------------------------------------------------

_search_label_ = localized_string(30002)

def search_dialog():
    return dialog.input(_search_label_)


# notify -----------------------------------------------------------------------

_notify_heading_ = localized_string(30000)

def notify(message, heading=_notify_heading_, icon=xbmcgui.NOTIFICATION_ERROR,
           time=2000):
    if isinstance(message, int):
        message = localized_string(message)
    dialog.notification(heading, message, icon, time)

