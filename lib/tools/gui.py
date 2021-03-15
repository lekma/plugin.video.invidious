# -*- coding: utf-8 -*-


__all__ = [
    "getWindowId", "ICONINFO", "ICONWARNING", "ICONERROR", "notify",
    "selectDialog", "inputDialog", "contextMenu", "ListItem"
]


import xbmcgui

from .addon import __addon_name__,__addon_icon__,  maybeLocalize


# getWindowId ------------------------------------------------------------------

def getWindowId():
    return xbmcgui.getCurrentWindowId()


# notify -----------------------------------------------------------------------

ICONINFO = xbmcgui.NOTIFICATION_INFO
ICONWARNING = xbmcgui.NOTIFICATION_WARNING
ICONERROR = xbmcgui.NOTIFICATION_ERROR

def notify(message, heading=__addon_name__, icon=__addon_icon__, time=5000):
    xbmcgui.Dialog().notification(
        maybeLocalize(heading), maybeLocalize(message), icon=icon, time=time
    )


# select -----------------------------------------------------------------------

def selectDialog(_list_, heading=__addon_name__, multi=False, **kwargs):
    if multi:
        return xbmcgui.Dialog().multiselect(
            maybeLocalize(heading), _list_, **kwargs
        )
    return xbmcgui.Dialog().select(maybeLocalize(heading), _list_, **kwargs)


# input ------------------------------------------------------------------------

def inputDialog(heading=__addon_name__, **kwargs):
    return xbmcgui.Dialog().input(maybeLocalize(heading), **kwargs)


# contextmenu ------------------------------------------------------------------

def contextMenu(_list_):
    return xbmcgui.Dialog().contextmenu(_list_)


# listitem ---------------------------------------------------------------------

class ListItem(xbmcgui.ListItem):

    def __new__(cls, label, path, **kwargs):
        return super().__new__(cls, label=label, path=path)

    def __init__(self, label, path, isFolder=False, isPlayable=True,
                 infos=None, streamInfos=None, contextMenus=None, **art):
        super().__init__(label=label, path=path)
        self.setIsFolder(isFolder)
        self.setIsPlayable(False if isFolder else isPlayable)
        if infos:
            for info in infos.items():
                self.setInfo(*info)
        if streamInfos:
            for streamInfo in streamInfos.items():
                self.addStreamInfo(*streamInfo)
        if contextMenus:
            self.addContextMenuItems(contextMenus)
        if art:
            self.setArt(art)

    def setIsFolder(self, isFolder):
        super().setIsFolder(isFolder)
        #self.setProperty("IsFolder", str(isFolder).lower())
        self.isFolder = isFolder

    def setIsPlayable(self, isPlayable):
        self.setProperty("IsPlayable", str(isPlayable).lower())
        self.isPlayable = isPlayable

    def asItem(self):
        return (self.getPath(), self, self.isFolder)

