# -*- coding: utf-8 -*-


from nuttig import (
    localizedString, ListItem, buildUrl, getMedia, yesnoDialog
)


# misc useful items ------------------------------------------------------------

def __makeItem__(label, url, art=None, isFolder=True, properties=None, **kwargs):
    label = localizedString(label)
    return ListItem(
        label,
        buildUrl(url, **kwargs),
        isFolder=isFolder,
        isPlayable=False,
        properties=properties,
        infoLabels={"video": {"title": label, "plot": label}},
        thumb=art,
        poster=art,
        icon=art
    )


# settings item
def settingsItem(url, **kwargs):
    return __makeItem__(
        5, url, art="DefaultAddonService.png", isFolder=False, **kwargs
    )


# newQuery item
def newQueryItem(url, **kwargs):
    return __makeItem__(30410, url, art="DefaultAddSource.png", **kwargs)


# channels item
def channelsItem(url, **kwargs):
    return __makeItem__(30110, url, art="DefaultArtist.png", **kwargs)


# more item
__more_art__ = getMedia("more")

def moreItem(url, **kwargs):
    return __makeItem__(
        30001,
        url,
        art=__more_art__,
        properties={"SpecialSort": "bottom"},
        **kwargs
    )


# dialogs ----------------------------------------------------------------------

def confirm():
    return yesnoDialog(localizedString(90001))
