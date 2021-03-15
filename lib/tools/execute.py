# -*- coding: utf-8 -*-


__all__ = [
    "executeBuiltin", "executeJSONRPC",
    "containerRefresh", "containerUpdate", "playMedia", "addFavourite"
]


from json import dumps, loads

import xbmc


# executeBuiltin ---------------------------------------------------------------

def executeBuiltin(function, *args):
    xbmc.executebuiltin(f"{function}({','.join(args)})")


# executeJSONRPC ---------------------------------------------------------------

class JSONRPCError(Exception):

    def __init__(self, error):
        message = f"[{error['code']}] {error['message']}".rstrip(".")
        if (data := error.get("data")):
            message = f"{message} {self.__data__(data)}"
        super().__init__(message)

    def __data__(self, data):
        message = f"in {data['method']}"
        if (stack := data.get("stack")):
            message = f"{message} {self.__stack__(stack)}"
        return message

    def __stack__(self, stack):
        return f"({stack['message']} ('{stack['name']}'))"


def executeJSONRPC(method, **params):
    request = {"id": 1, "jsonrpc": "2.0", "method": method, "params": params}
    if (error := loads(xbmc.executeJSONRPC(dumps(request))).get("error")):
        raise JSONRPCError(error)


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

