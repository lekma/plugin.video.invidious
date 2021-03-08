# -*- coding: utf-8 -*-


from tools import localizedString, ListItem, buildUrl, getMedia, executeBuiltin


# misc useful items ------------------------------------------------------------

def __makeItem__(label, url, art=None, isFolder=True, **kwargs):
    label = localizedString(label)
    return ListItem(
        label,
        buildUrl(url, **kwargs),
        isFolder=isFolder,
        isPlayable=False,
        infos={"video": {"title": label, "plot": label}},
        poster=art,
        icon=art
    )


# settings item
def settingsItem(url, **kwargs):
    return __makeItem__(
        30100, url, "icons/settings/system.png", isFolder=False, **kwargs
    )


# more item
__more_art__ = getMedia("more")

def moreItem(url, **kwargs):
    return __makeItem__(30099, url, __more_art__, **kwargs)


# newSearch item
def newSearchItem(url, **kwargs):
    return __makeItem__(30062, url, "DefaultAddSource.png", **kwargs)


# playlists item
def playlistsItem(url, **kwargs):
    return __makeItem__(30005, url, "DefaultPlaylist.png", **kwargs)


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

