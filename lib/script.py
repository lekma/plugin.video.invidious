# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import sys
import json

from kodi_six import xbmc

from client import client
from iac import JSONRPCError
from utils import getAddonId


_channel_action_ = "plugin://{}/?action=channel&authorId={{}}".format(getAddonId())


# goToChannel ------------------------------------------------------------------

def goToChannel(authorId):
    xbmc.executebuiltin(
        "Container.Update({})".format(_channel_action_.format(authorId)))


# addChannelToFavourites -------------------------------------------------------

_request_ = {
    "id": 1,
    "jsonrpc": "2.0",
    "method": "Favourites.AddFavourite"
}

_request_params_ = {
    "type": "window",
    "window": "videos"
}

def executeJSONRPC(request):
    error = json.loads(xbmc.executeJSONRPC(json.dumps(request))).get("error")
    if error:
        raise JSONRPCError(error)

def addChannelToFavourites(authorId):
    channel = client.channel_(authorId)
    params = dict(_request_params_,
                  title=channel.author, thumbnail=channel.thumbnail,
                  windowparameter=_channel_action_.format(authorId))
    executeJSONRPC(dict(_request_, params=params))


# __main__ ---------------------------------------------------------------------

_dispatch_ = {
    "goToChannel": goToChannel,
    "addChannelToFavourites": addChannelToFavourites
}

def dispatch(name, *args):
    action = _dispatch_.get(name)
    if not action or not callable(action):
        raise Exception("Invalid script action '{}'".format(name))
    action(*args)


if __name__ == "__main__":

    dispatch(*sys.argv[1:])

