# -*- coding: utf-8 -*-


from sys import argv
from urllib.parse import unquote_plus

from iapc import Client
from nuttig import containerUpdate, getAddonId, playMedia


# play -------------------------------------------------------------------------

def playFromYouTube(videoId):
    playMedia(
        f"plugin://{getAddonId()}/?action=play&yt=true&videoId={videoId}"
    )

def playWithYouTube(videoId):
    playMedia(
        f"plugin://plugin.video.youtube/play/?incognito=true&video_id={videoId}"
    )


# goToChannel ------------------------------------------------------------------

def goToChannel(channelId):
    containerUpdate(
        f"plugin://{getAddonId()}/?action=channel&channelId={channelId}"
    )


# instance ---------------------------------------------------------------------

def selectInstance():
    return Client().instance.selectInstance()

def selectLocale():
    return Client().instance.selectLocale()

def selectRegion():
    return Client().instance.selectRegion()


# feed -------------------------------------------------------------------------

def addChannelToFeed(channelId, channel):
    return Client().feed.addChannel(channelId, channel)

def removeChannelFromFeed(channelId):
    return Client().feed.removeChannel(channelId)

def clearChannelsFromFeed():
    return Client().feed.clearChannels()


# search -----------------------------------------------------------------------

def updateQueryType(q):
    return Client().search.updateQueryType(q)

def updateQuerySort(q):
    return Client().search.updateQuerySort(q)

def removeQuery(q):
    return Client().search.removeQuery(q)

def clearHistory():
    return Client().search.clearHistory()


# __main__ ---------------------------------------------------------------------

__scripts__ = {
    "playFromYouTube": playFromYouTube,
    "playWithYouTube": playWithYouTube,
    "goToChannel": goToChannel,
    "selectInstance": selectInstance,
    "selectLocale": selectLocale,
    "selectRegion": selectRegion,
    "addChannelToFeed": addChannelToFeed,
    "removeChannelFromFeed": removeChannelFromFeed,
    "clearChannelsFromFeed": clearChannelsFromFeed,
    "updateQueryType": updateQueryType,
    "updateQuerySort": updateQuerySort,
    "removeQuery": removeQuery,
    "clearHistory": clearHistory
}

def dispatch(name, *args):
    if (not (script := __scripts__.get(name)) or not callable(script)):
        raise Exception(f"Invalid script '{name}'")
    script(*(unquote_plus(arg) for arg in args))


if __name__ == "__main__":
    dispatch(*argv[1:])
