# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


from datetime import datetime

from six import string_types, iteritems, with_metaclass, raise_from
from six.moves.urllib.parse import quote_plus

from utils import ListItem, buildUrl, localizedString, getAddonId


# ------------------------------------------------------------------------------
# base types
# ------------------------------------------------------------------------------

def _date_(value):
    if isinstance(value, int):
        return datetime.fromtimestamp(value)
    return value

def _json_(name, func):
    def getter(obj):
        return func(obj.__getattr__(name))
    return property(getter)


class InvidiousType(type):

    __json__ = {"__date__": _date_}
    __attr_error__ = "'{}' object has no attribute '{{}}'"

    def __new__(cls, name, bases, namespace, **kwargs):
        namespace.setdefault("__slots__", set())
        namespace.setdefault("__attr_error__", cls.__attr_error__.format(name))
        for _name, _func in iteritems(namespace.pop("__json__", dict())):
            namespace[_name] = _json_(_name, _func)
        for _type, _func in iteritems(cls.__json__):
            for _name in namespace.pop(_type, set()):
                namespace[_name] = _json_(_name, _func)
        return type.__new__(cls, name, bases, namespace, **kwargs)


class InvidiousObject(with_metaclass(InvidiousType, object)):

    __slots__ = {"__data__"}

    def __new__(cls, data):
        if isinstance(data, dict):
            if not data:
                return None
            return super(InvidiousObject, cls).__new__(cls)
        return data

    def __init__(self, data):
        self.__data__ = data

    def __getitem__(self, name):
        return self.__data__[name]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise_from(AttributeError(self.__attr_error__.format(name)), None)

    def __repr__(self):
        try:
            _repr_ = self._repr_
        except AttributeError:
            return super(InvidiousObject, self).__repr__()
        else:
            return _repr_.format(self)


# folders ----------------------------------------------------------------------

_folders_schema_ = {
    "search": {
        "": {
            "id": 30002
        },
        "videos": {
            "id": 30003,
            "kwargs": {"type": "video"}
        },
        "channels": {
            "id": 30004,
            "kwargs": {"type": "channel"}
        },
        "playlists": {
            "id": 30005,
            "kwargs": {"type": "playlist"}
        },
        "new": {
            "id": 30062,
            "action": "new_search"
        }
    },
    "playlists": {
        "": {
            "id": 30005
        }
    },
    "live": {
        "": {
            "id": 30006,
            "action": "playlists",
            "kwargs": {"authorId": "UC4R8DWoMoI7CAwX8_LjQHig"}
        }
    },
    "top": {
        "": {
            "id": 30007
        }
    },
    "popular": {
        "": {
            "id": 30008
        }
    },
    "trending": {
        "": {
            "id": 30009
        },
        "music": {
            "id": 30010,
            "kwargs": {"type": "Music"}
        },
        "gaming": {
            "id": 30011,
            "kwargs": {"type": "Gaming"}
        },
        "news": {
            "id": 30012,
            "kwargs": {"type": "News"}
        },
        "movies": {
            "id": 30013,
            "kwargs": {"type": "Movies"}
        }
    },
    "music": {
        "": {
            "id": 30010,
            "action": "playlists",
            "kwargs": {"authorId": "UC-9-kyTW8ZkZNDHQJ6FgpwQ"}
        }
    },
    "gaming": {
        "": {
            "id": 30011,
            "action": "playlists",
            "kwargs": {"authorId": "UCOpNcN46UbXVtpKMrmU4Abg"}
        }
    },
    "news": {
        "": {
            "id": 30012,
            "action": "playlists",
            "kwargs": {"authorId": "UCYfdidRxbB8Qhf0Nx7ioOYw"}
        }
    },
    "feed": {
        "": {
            "id": 30014
        }
    }
}


_home_folders_ = (
    {"type": "feed"},
    {"type": "top"},
    {"type": "popular"},
    {"type": "trending"},
    {"type": "music"},
    {"type": "gaming"},
    {"type": "news"},
    {"type": "live"},
    {"type": "search"}
)


_trending_styles_ = ("music", "gaming", "news", "movies")


_search_styles_ = ("videos", "channels", "playlists")


class Folder(InvidiousObject):

    @property
    def style(self):
        try:
            return self["style"] or ""
        except KeyError:
            return ""

    def item(self, url, **kwargs):
        folder = _folders_schema_[self.type][self.style]
        label = folder["id"]
        if isinstance(label, int):
            label = localizedString(label)
        action = folder.get("action", self.type)
        kwargs.update(folder.get("kwargs", {}))
        plot = folder.get("plot", label)
        if isinstance(plot, int):
            plot = localizedString(plot)
        return ListItem(
            label, buildUrl(url, action=action, **kwargs), isFolder=True,
            infos={"video": {"title": label, "plot": plot}})


# ------------------------------------------------------------------------------
# Invidious objects
# ------------------------------------------------------------------------------

class InvidiousItem(InvidiousObject):

    _menus_ = []

    def plot(self):
        return self._plot_.format(self)

    @classmethod
    def menus(cls, **kwargs):
        return [(localizedString(label).format(**kwargs),
                 action.format(addonId=getAddonId(), **kwargs))
                for label, action in cls._menus_]


class Thumbnails(object):

    def __new__(cls, thumbnails):
        if thumbnails:
            return super(Thumbnails, cls).__new__(cls, thumbnails)
        return None


# videos -----------------------------------------------------------------------

class VideoThumbnails(Thumbnails):

    def __init__(self, thumbnails):
        if isinstance(thumbnails[0], list):
            thumbnails = thumbnails[0]
        for thumbnail in thumbnails:
            if isinstance(thumbnail, list):
                thumbnail = thumbnail[0]
            setattr(self, thumbnail["quality"], thumbnail["url"])


class BaseVideo(InvidiousItem):

    __json__ = {"videoThumbnails": VideoThumbnails}
    __date__ = {"published"}
    _repr_ = "BaseVideo({0.videoId})"
    _infos_ = {"mediatype": "video"}
    _plot_ = localizedString(30056)
    _menus_ = [
        (30033, "RunScript({addonId},playWithYouTube,{videoId})"),
        (30031, "RunScript({addonId},goToChannel,{authorId})"),
        (30032, "RunScript({addonId},addChannelToFavourites,{authorId})"),
        (30034, "RunScript({addonId},addChannelToFeed,{authorId},{author})")
    ]

    @property
    def _infos(self):
        return self._infos_

    @property
    def _title(self):
        return self.title

    def _item(self, path):
        return ListItem(
            self._title,
            path,
            infos={"video": dict(self._infos, title=self.title, plot=self.plot())},
            streamInfos={"video": {"duration": self.lengthSeconds}},
            contextMenus=self.menus(authorId=self.authorId,
                                    author=quote_plus(self.author.encode("utf-8")),
                                    videoId=self.videoId),
            thumb=getattr(self.videoThumbnails, "sddefault", ""))

    def item(self, url, action):
        return self._item(buildUrl(url, action=action, videoId=self.videoId))


class ShortVideo(BaseVideo):

    _repr_ = "ShortVideo({0.videoId})"
    _plot_ = localizedString(30057)


class StdVideo(ShortVideo):

    _repr_ = "StdVideo({0.videoId})"
    _plot_ = localizedString(30058)


class Video(StdVideo):

    _repr_ = "Video({0.videoId})"
    _plot_ = localizedString(30058)
    _live_ = localizedString(30059)

    @property
    def _infos(self):
        if self.liveNow:
            return dict(self._infos_, playcount=0)
        return super(Video, self)._infos

    @property
    def _title(self):
        if self.liveNow:
            return self._live_.format(self)
        return super(Video, self)._title


# channels ---------------------------------------------------------------------

class AuthorThumbnails(Thumbnails):

    def __init__(self, thumbnails):
        for thumbnail in thumbnails:
            setattr(self, str(thumbnail["height"]), thumbnail["url"])


class Channel(InvidiousItem):

    __json__ = {"authorThumbnails": AuthorThumbnails}
    _repr_ = "Channel({0.author})"
    _plot_ = localizedString(30060)
    _menus_ = [
        (30034, "RunScript({addonId},addChannelToFeed,{authorId},{author})")
    ]

    @property
    def thumbnail(self):
        return getattr(self.authorThumbnails, "512", "")

    def item(self, url, action):
        return ListItem(
            self.author,
            buildUrl(url, action=action, authorId=self.authorId),
            isFolder=True,
            infos={"video": {"plot": self.plot()}},
            contextMenus=self.menus(authorId=self.authorId,
                                    author=quote_plus(self.author.encode("utf-8"))),
            poster=self.thumbnail)


# playlists --------------------------------------------------------------------

class Playlist(InvidiousItem):

    _repr_ = "Playlist({0.playlistId})"
    _plot_ = localizedString(30061)

    def item(self, url, action):
        return ListItem(
            self.title,
            buildUrl(url, action=action, playlistId=self.playlistId),
            isFolder=True,
            infos={"video": {"plot": self.plot()}},
            poster=self.playlistThumbnail)


# ------------------------------------------------------------------------------
# lists, collections
# ------------------------------------------------------------------------------

class InvidiousItems(list):

    _ctor_ = InvidiousObject
    _content_ = "videos"
    _category_ = None

    def __init__(self, items, limit=0, content=None, category=None):
        super(InvidiousItems, self).__init__((self._ctor_(item) for item in items))
        self.more = (len(self) >= limit) if limit else False
        self.content = content or self._content_
        self.category = category or self._category_

    def items(self, *args):
        return (item.item(*args) for item in self if item)


class Folders(InvidiousItems):

    _ctor_ = Folder


class Home(Folders):

    def __init__(self):
        super(Home, self).__init__(_home_folders_)


class BaseVideos(InvidiousItems):

    _ctor_ = BaseVideo


class ShortVideos(InvidiousItems):

    _ctor_ = ShortVideo


class StdVideos(InvidiousItems):

    _ctor_ = StdVideo


class Videos(InvidiousItems):

    _ctor_ = Video


class Channels(InvidiousItems):

    _ctor_ = Channel


class Playlists(InvidiousItems):

    _ctor_ = Playlist


class ChannelPlaylists(InvidiousItems):

    _ctor_ = Playlist

    def __init__(self, playlists, category=None, continuation=None):
        super(ChannelPlaylists, self).__init__(playlists, category=category)
        if continuation:
            self.more = True
            self.continuation = continuation

