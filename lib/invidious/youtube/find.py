# -*- coding: utf-8 -*-


from re import search


class MatchError(Exception):

    def __init__(self, msg):
        super().__init__(f"No matches found for {msg}")


class PatternsError(MatchError):

    def __init__(self, *patterns):
        super().__init__(f"patterns: {patterns}")


def __find__(pattern, string):
    if (match := search(pattern, string)):
        return match
    raise PatternsError(pattern)


def findInValues(values, pattern, callback):
    for value in values:
        if isinstance(value, str) and (pattern in value):
            callback(value)
        elif isinstance(value, list):
            findInValues(value, pattern, callback)
        elif isinstance(value, dict):
            findInValues(value.values(), pattern, callback)

