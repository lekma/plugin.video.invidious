# -*- coding: utf-8 -*-


__all__ = ["Playlist", "Playlists"]


from iapc.tools import localizedString, ListItem, buildUrl

from .base import Url, Item, Items


# ------------------------------------------------------------------------------
# Playlists

class Playlist(Item):

    __plot__ = localizedString(30061)

    @property
    def thumbnail(self):
        return Url(self.playlistThumbnail) or "DefaultPlaylist.png"

    def getItem(self, url, action):
        return ListItem(
            self.title,
            buildUrl(url, action=action, playlistId=self.playlistId),
            isFolder=True,
            infoLabels={"video": {"title": self.title, "plot": self.plot}},
            poster=self.thumbnail,
            thumb=self.thumbnail
        )


class Playlists(Items):

    __ctor__ = Playlist

