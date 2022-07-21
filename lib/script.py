# -*- coding: utf-8 -*-


from sys import argv
from urllib.parse import unquote_plus
import json

from iapc.tools import (
    getAddonId, selectDialog, getSetting, setSetting,
    containerUpdate, addFavourite, playMedia
)

from invidious.client import client
from invidious.persistence import channel_feed
from invidious.search import removeSearchQuery, clearSearchHistory, updateSortBy
from invidious.youtube.params import languages, locations


__plugin_url__ = f"plugin://{getAddonId()}"


# channel stuff ----------------------------------------------------------------

__channel_url__ = f"{__plugin_url__}/?action=channel&authorId={{}}"

def goToChannel(authorId):
    containerUpdate(__channel_url__.format(authorId))

def addChannelToFavourites(authorId):
    channel = client.__channel__(authorId)
    addFavourite(
        channel.author, "window",
        window="videos", thumbnail=channel.thumbnail,
        windowparameter=__channel_url__.format(authorId)
    )


# playWithYouTube --------------------------------------------------------------

__youtube_url__ = f"{__plugin_url__}/?action=video&youtube=true&videoId={{}}"

def playWithYouTube(videoId):
    playMedia(__youtube_url__.format(videoId))


# selectInstance ---------------------------------------------------------------

def selectInstance():
    instance = getSetting("instance", str)
    instances = client.instances(sort_by="health")
    if instances:
        preselect = instances.index(instance) if instance in instances else -1
        index = selectDialog(instances, heading=30105, preselect=preselect)
        if index >= 0:
            setSetting("instance", instances[index], str)


# selectLanguage ---------------------------------------------------------------

def selectLanguage():
    hl = getSetting("hl", str)
    keys = list(languages.keys())
    values = list(languages.values())
    preselect = keys.index(hl) if hl in languages else -1
    if (index := selectDialog(values, heading=30125, preselect=preselect)) >= 0:
        setSetting("hl", keys[index], str)
        setSetting("hl.text", values[index], str)


# selectLocation ---------------------------------------------------------------

def selectLocation():
    gl = getSetting("gl", str)
    keys = list(locations.keys())
    values = list(locations.values())
    preselect = keys.index(gl) if gl in locations else -1
    if (index := selectDialog(values, heading=30127, preselect=preselect)) >= 0:
        setSetting("gl", keys[index], str)
        setSetting("gl.text", values[index], str)


# feed stuff -------------------------------------------------------------------

def addChannelToFeed(authorId, author):
    channel_feed.add(authorId, author)

def removeChannelsFromFeed():
    if (indices := selectDialog(list(channel_feed.values()), heading=30014, multi=True)):
        keys = list(channel_feed.keys())
        channel_feed.remove(*(keys[index] for index in indices))


def newpipeImport():
    newpipe_filepath = getSetting("newpipe.path")

    with open(newpipe_filepath, 'r', encoding='utf-8') as fp:
        newpipe_dict = json.load(fp)
        newpipe_subscriptions = newpipe_dict.get('subscriptions', ())
        channel_feed.clear()
        for item in newpipe_subscriptions:
            item_id = item['url'].split('/')[-1]
            channel_feed.add(item_id, item['name'])


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
    "newpipeImport": newpipeImport,
    "removeSearchQuery": removeSearchQuery,
    "clearSearchHistory": clearSearchHistory,
    "updateSortBy": updateSortBy
}

def dispatch(name, *args):

    if (
        not (action := __dispatch__.get(name)) or
        not callable(action)
    ):
        raise Exception(f"Invalid script '{name}'")
    action(*(unquote_plus(arg) for arg in args))


if __name__ == "__main__":
    dispatch(*argv[1:])

