# -*- coding: utf-8 -*-


from time import time

from iapc import public
from nuttig import containerRefresh, localizedString, notify, ICONINFO

from invidious.persistence import IVFeedChannels
from invidious.utils import confirm


# ------------------------------------------------------------------------------
# IVFeed

class IVFeed(object):

    def __init__(self, logger, instance, timeout=1800):
        self.logger = logger.getLogger(component="feed")
        self.__instance__ = instance
        self.__channels__ = IVFeedChannels()
        self.__timeout__ = timeout
        self.__last__ = time()
        self.__keys__ = None
        self.__videos__ = []

    def __setup__(self):
        self.__keys__ = None

    def __stop__(self):
        self.__instance__ = None
        self.logger.info("stopped")

    # --------------------------------------------------------------------------

    def __invalid__(self, keys):
        return (self.__keys__ != keys)

    def __expired__(self):
        return ((time() - self.__last__) > self.__timeout__)

    def invalid(self):
        if (invalid := self.__invalid__(keys := set(self.__channels__.keys()))):
            self.__keys__ = keys
        if (invalid or self.__expired__()):
            return self.__keys__

    def update(self, videos):
        self.__videos__ = sorted(
            videos, key=lambda x: x["published"], reverse=True
        )
        self.__last__ = time()

    def page(self, limit, page):
        videos, next = (
            self.__videos__[:(fence := (limit * page))],
            self.__videos__[fence:]
        )
        return (
            videos[(limit * (page - 1)):],
            {"page": (page + 1)} if next else None
        )

    # feed ---------------------------------------------------------------------

    @public
    def feed(self, limit, page=1):
        if (
            ((page := int(page)) == 1) and
            ((keys := self.invalid()) is not None)
        ):
            self.update(self.__instance__.__feeds__(keys))
        return self.page(limit, page)

    # channels -----------------------------------------------------------------

    @public
    def channels(self):
        return list(self.__instance__.__channels__(self.__channels__.keys()))

    @public
    def addChannel(self, key, value):
        self.__channels__.add(key, value)
        notify(localizedString(90002).format(value), icon=ICONINFO, time=1000)

    @public
    def removeChannel(self, key):
        self.__channels__.remove(key)
        containerRefresh()

    @public
    def clearChannels(self):
        if confirm():
            self.__channels__.clear()
            containerRefresh()

