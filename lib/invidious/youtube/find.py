# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import re


class MatchError(Exception):

    __msg__ = "No matches found for {}"

    def __init__(self, msg):
        super(MatchError, self).__init__(self.__msg__.format(msg))


class PatternsError(MatchError):

    __patterns__ = "patterns: {}"

    def __init__(self, *patterns):
        super(PatternsError, self).__init__(self.__patterns__.format(patterns))


def __find__(pattern, string):
    match = re.search(pattern, string)
    if match:
        return match
    raise PatternsError(pattern)


def findInValues(values, pattern, callback):
    for value in values:
        if isinstance(value, (str, unicode)) and (pattern in value):
            callback(value)
        elif isinstance(value, list):
            findInValues(value, pattern, callback)
        elif isinstance(value, dict):
            findInValues(value.values(), pattern, callback)

