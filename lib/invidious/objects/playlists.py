# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


__all__ = ["Playlist", "Playlists"]


from tools import localizedString, ListItem, buildUrl

from .base import Item, Items


# ------------------------------------------------------------------------------
# Playlists
# ------------------------------------------------------------------------------

class Playlist(Item):

    __plot__ = localizedString(30061)

    @property
    def thumbnail(self):
        return self.playlistThumbnail or "DefaultPlaylist.png"

    def getItem(self, url, action):
        return ListItem(
            self.title,
            buildUrl(url, action=action, playlistId=self.playlistId),
            isFolder=True,
            infos={"video": {"title": self.title, "plot": self.plot}},
            poster=self.thumbnail
        )


class Playlists(Items):

    __ctor__ = Playlist

