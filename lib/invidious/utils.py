# -*- coding: utf-8 -*-





from tools import (
    localizedString, ListItem, buildUrl, getMedia,
    executeBuiltin, executeJSONRPC
)


# misc useful items ------------------------------------------------------------

def _makeItem(label, url, thumb=None, isFolder=True, **kwargs):
    label = localizedString(label)
    return ListItem(
        label,
        buildUrl(url, **kwargs),
        isFolder=isFolder,
        isPlayable=False,
        infos={"video": {"title": label, "plot": label}},
        poster=thumb
    )

# settings item
def settingsItem(url, **kwargs):
    return _makeItem(
        30100, url, "icons/settings/system.png", isFolder=False, **kwargs
    )

# more item
def moreItem(url, **kwargs):
    return _makeItem(30099, url, getMedia("more"), **kwargs)

# newSearch item
def newSearchItem(url, **kwargs):
    return _makeItem(30062, url, "DefaultAddSource.png", **kwargs)

# playlists item
def playlistsItem(url, **kwargs):
    return _makeItem(30005, url, "DefaultPlaylist.png", **kwargs)


# misc execute utils -----------------------------------------------------------

# containerRefresh
def containerRefresh(*args):
    executeBuiltin("Container.Refresh", *args)

# containerUpdate
def containerUpdate(*args):
    executeBuiltin("Container.Update", *args)

# playMedia
def playMedia(*args):
    executeBuiltin("PlayMedia", *args)

# addFavourite
def addFavourite(title, type, **kwargs):
    executeJSONRPC("Favourites.AddFavourite", title=title, type=type, **kwargs)

# setFocus
def setFocus(*args):
    executeBuiltin("Control.SetFocus", *args)

