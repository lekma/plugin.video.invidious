# -*- coding: utf-8 -*-





__all__ = ["Channel", "Channels"]


from six.moves.urllib.parse import quote_plus

from tools import localizedString, ListItem, buildUrl

from .base import Url, Thumbnails, Item, Items


# ------------------------------------------------------------------------------
# Channels
# ------------------------------------------------------------------------------

class ChannelThumbnails(Thumbnails):

    def __init__(self, thumbnails):
        for thumbnail in thumbnails:
            setattr(self, str(thumbnail["height"]), Url(thumbnail["url"]))


class Channel(Item):

    __transform__ = {"authorThumbnails": ChannelThumbnails}
    __plot__ = "{0.author}\n\n{0.description}"

    __menus__ = [
        (30034, "RunScript({addonId},addChannelToFeed,{authorId},{author})")
    ]

    @property
    def thumbnail(self):
        return getattr(self.authorThumbnails, "512", "DefaultArtist.png")

    def getItem(self, url, action):
        return ListItem(
            self.author,
            buildUrl(url, action=action, authorId=self.authorId),
            isFolder=True,
            infos={"video": {"title": self.author, "plot": self.plot}},
            contextMenus=self.menus(
                authorId=self.authorId,
                author=quote_plus(self.author.encode("utf-8"))
            ),
            poster=self.thumbnail
        )


class Channels(Items):

    __ctor__ = Channel

