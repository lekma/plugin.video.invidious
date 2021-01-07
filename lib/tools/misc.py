# -*- coding: utf-8 -*-





__all__ = [
    "formatException", "parseQuery", "buildUrl",
    "dumpObject", "loadObject"
]


from sys import exc_info
from traceback import format_exception
from pickle import dump, load
from os.path import exists

from six import u, text_type, iteritems
from six.moves.urllib.parse import parse_qsl, urlencode


# encode exception for logging -------------------------------------------------

def formatException(limit=None):
    try:
        etype, value, tb = exc_info()
        lines = format_exception(etype, value, tb, limit)
        lines, line = lines[:-1], lines[-1]
        lines.append(u(line).encode("utf-8"))
        return "".join(line.decode("utf-8") for line in lines)
    finally:
        etype = value = tb = None


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
    if query.startswith("?"):
        query = query[1:]
    return {k: parseValue(v) for k, v in parse_qsl(query)}


#  buildUrl --------------------------------------------------------------------

def buildUrl(*args, **kwargs):
    params = {
        k: v.encode("utf-8") if isinstance(v, text_type) else v
        for k, v in iteritems(kwargs)
    }
    if params:
        return "?".join(("/".join(args), urlencode(params)))
    return "/".join(args)


# pickle -----------------------------------------------------------------------

def dumpObject(obj, path):
    with open(path, "wb+") as f:
        dump(obj, f, -1)

def loadObject(path, default=None):
    if exists(path):
        with open(path, "rb") as f:
            return load(f)
    return default
