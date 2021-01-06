# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import sys

from six import iterkeys, itervalues, iteritems

from tools import getAddonId, selectDialog, getSetting, setSetting

from invidious.client import client
from invidious.persistence import (
    addChannelToFeed, removeChannelsFromFeed,
    removeSearchQuery, clearSearchHistory, updateSortBy
)
from invidious.utils import containerUpdate, addFavourite, playMedia
from invidious.youtube.params import languages, locations


# channel stuff ----------------------------------------------------------------

__channel_url__ = "plugin://{}/?action=channel&authorId={{}}".format(getAddonId())

def goToChannel(authorId):
    containerUpdate(__channel_url__.format(authorId))

def addChannelToFavourites(authorId):
    channel = client._channel(authorId)
    addFavourite(
        channel.author, "window",
        window="videos", thumbnail=channel.thumbnail,
        windowparameter=__channel_url__.format(authorId)
    )


# playWithYouTube --------------------------------------------------------------

_youtube_url_ = "plugin://{}/?action=video&youtube=true&videoId={{}}".format(getAddonId())

def playWithYouTube(videoId):
    playMedia(_youtube_url_.format(videoId))


# selectInstance ---------------------------------------------------------------

def selectInstance():
    instance = getSetting("instance", unicode)
    instances = client._instances(sort_by="health")
    if instances:
        preselect = instances.index(instance) if instance in instances else -1
        index = selectDialog(instances, heading=30105, preselect=preselect)
        if index >= 0:
            setSetting("instance", instances[index], unicode)


# selectLanguage ---------------------------------------------------------------

def selectLanguage():
    hl = getSetting("youtube.hl", unicode)
    keys = list(iterkeys(languages))
    values = list(itervalues(languages))
    preselect = keys.index(hl) if hl in languages else -1
    index = selectDialog(values, heading=30125, preselect=preselect)
    if index >= 0:
        setSetting("youtube.hl", keys[index], unicode)
        setSetting("youtube.hl.text", values[index], unicode)


# selectLocation ---------------------------------------------------------------

def selectLocation():
    gl = getSetting("youtube.gl", unicode)
    keys = list(iterkeys(locations))
    values = list(itervalues(locations))
    preselect = keys.index(gl) if gl in locations else -1
    index = selectDialog(values, heading=30127, preselect=preselect)
    if index >= 0:
        setSetting("youtube.gl", keys[index], unicode)
        setSetting("youtube.gl.text", values[index], unicode)


# __main__ ---------------------------------------------------------------------

__dispatch__ = {
    "goToChannel": goToChannel,
    "addChannelToFavourites": addChannelToFavourites,
    "playWithYouTube": playWithYouTube,
    "selectInstance": selectInstance,
    "selectLanguage": selectLanguage,
    "selectLocation": selectLocation,
    "addChannelToFeed": addChannelToFeed,
    "removeChannelsFromFeed": removeChannelsFromFeed,
    "removeSearchQuery": removeSearchQuery,
    "clearSearchHistory": clearSearchHistory,
    "updateSortBy": updateSortBy
}

def dispatch(name, *args):
    action = __dispatch__.get(name)
    if not action or not callable(action):
        raise Exception("Invalid script '{}'".format(name))
    action(*args)


if __name__ == "__main__":
    dispatch(*sys.argv[1:])

