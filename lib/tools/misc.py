# -*- coding: utf-8 -*-


__all__ = ["parseQuery", "buildUrl", "dumpObject", "loadObject"]


from os.path import exists
from pickle import dump, load
from urllib.parse import parse_qsl, urlencode


# parseQuery -------------------------------------------------------------------

__parse_consts__ = {
    "none": None,
    "true": True,
    "false": False
}

def parseValue(value):
    try:
        return __parse_consts__[value.lower()]
    except KeyError:
        return value

def parseQuery(query):
    return {
        k: parseValue(v)
        for k, v in parse_qsl(query[1:] if query.startswith("?") else query)
    }


#  buildUrl --------------------------------------------------------------------

def buildUrl(*args, **kwargs):
    url = "/".join(args)
    return "?".join((url, urlencode(kwargs))) if kwargs else url


# pickle -----------------------------------------------------------------------

def dumpObject(obj, path):
    with open(path, "wb+") as f:
        dump(obj, f, -1)

def loadObject(path, default=None):
    if exists(path):
        with open(path, "rb") as f:
            return load(f)
    return default

