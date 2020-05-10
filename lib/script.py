# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import sys
import json

from kodi_six import xbmc

from client import client
from iapc import JSONRPCError
from utils import getAddonId, selectDialog, getSetting, setSetting


# utils ------------------------------------------------------------------------

# xbmc.executebuiltin
def _executeBuiltin_(function, *args):
    xbmc.executebuiltin("{}({})".format(function, ",".join(args)))


# xbmc.executeJSONRPC
_jsonrpc_request_ = {
    "id": 1,
    "jsonrpc": "2.0",
}

def _executeJSONRPC_(method, **kwargs):
    request = dict(_jsonrpc_request_, method=method, params=kwargs)
    error = json.loads(xbmc.executeJSONRPC(json.dumps(request))).get("error")
    if error:
        raise JSONRPCError(error)


# _containerUpdate -------------------------------------------------------------

def _containerUpdate(*args):
    _executeBuiltin_("Container.Update", *args)


# _addFavourite ----------------------------------------------------------------

def _addFavourite(title, type, **kwargs):
    _executeJSONRPC_("Favourites.AddFavourite", title=title, type=type, **kwargs)


# _playMedia -------------------------------------------------------------------

def _playMedia(*args):
    _executeBuiltin_("PlayMedia", *args)


# ------------------------------------------------------------------------------
# actions
# ------------------------------------------------------------------------------

_channel_url_ = "plugin://{}/?action=channel&authorId={{}}".format(getAddonId())


# goToChannel ------------------------------------------------------------------

def goToChannel(authorId):
    _containerUpdate(_channel_url_.format(authorId))


# addChannelToFavourites -------------------------------------------------------

def addChannelToFavourites(authorId):
    channel = client.channel_(authorId)
    _addFavourite(channel.author, "window",
                  window="videos", thumbnail=channel.thumbnail,
                  windowparameter=_channel_url_.format(authorId))


# playWithYouTube --------------------------------------------------------------

_youtube_url_ = "plugin://plugin.video.youtube/play/?incognito=true&video_id={}"

def playWithYouTube(videoId):
    _playMedia(_youtube_url_.format(videoId))


# selectInstance ---------------------------------------------------------------

def selectInstance():
    instance = getSetting("instance", unicode)
    instances = client.instances_(sort_by="health")
    if instances:
        preselect = instances.index(instance) if instance in instances else -1
        index = selectDialog(instances, preselect=preselect)
        if index >= 0:
            setSetting("instance", instances[index], unicode)


# __main__ ---------------------------------------------------------------------

_dispatch_ = {
    "goToChannel": goToChannel,
    "addChannelToFavourites": addChannelToFavourites,
    "playWithYouTube": playWithYouTube,
    "selectInstance": selectInstance
}

def dispatch(name, *args):
    action = _dispatch_.get(name)
    if not action or not callable(action):
        raise Exception("Invalid script action '{}'".format(name))
    action(*args)


if __name__ == "__main__":

    dispatch(*sys.argv[1:])

