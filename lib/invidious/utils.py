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
        5,
        url,
        art="DefaultAddonService.png",
        isFolder=False,
        properties={"SpecialSort": "bottom"},
        **kwargs
    )


# newQuery item
def newQueryItem(url, **kwargs):
    return __makeItem__(
        30410,
        url,
        art="DefaultAddSource.png",
        properties={"SpecialSort": "top"},
        **kwargs
    )


# channels item
def channelsItem(url, **kwargs):
    return __makeItem__(
        30110,
        url,
        art="DefaultArtist.png",
        properties={"SpecialSort": "top"},
        **kwargs
    )


# navigation item
__navigation_targets__ = {
    "previous": (30001, getMedia("previous"), {"SpecialSort": "top"}),
    "next": (30002, getMedia("next"), {"SpecialSort": "bottom"})
}

def navigationItem(target, url, **kwargs):
    label, art, properties = __navigation_targets__[target]
    return __makeItem__(
        label,
        url,
        art=art,
        properties=properties,
        **kwargs
    )


# dialogs ----------------------------------------------------------------------

def confirm():
    return yesnoDialog(localizedString(90001))
