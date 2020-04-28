# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


from datetime import datetime

from six import string_types, iteritems, with_metaclass, raise_from

from . import _folders_schema_, _home_folders_
from ..utils import ListItem, build_url, localized_string


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
            label = localized_string(label)
        action = folder.get("action", self.type)
        kwargs.update(folder.get("kwargs", {}))
        plot = folder.get("plot", "")
        if isinstance(plot, int):
            plot = localized_string(plot)
        return ListItem(
            label, build_url(url, action=action, **kwargs), isFolder=True,
            infos={"video": {"title": label, "plot": plot}})


# ------------------------------------------------------------------------------
# Invidious objects
# ------------------------------------------------------------------------------

class InvidiousItem(InvidiousObject):

    @classmethod
    def fields(cls):
        return set.union(*(getattr(c, "_fields_", set()) for c in cls.__mro__))

    def plot(self):
        return self._plot_.format(self)


class Thumbnails(object):

    def __new__(cls, thumbnails):
        if thumbnails:
            return super(Thumbnails, cls).__new__(cls, thumbnails)
        return None

# videos -----------------------------------------------------------------------

class VideoThumbnails(Thumbnails):

    def __init__(self, thumbnails):
        for thumbnail in thumbnails:
            setattr(self, thumbnail["quality"], thumbnail["url"])


class BaseVideo(InvidiousItem):

    __json__ = {"videoThumbnails": VideoThumbnails}
    __date__ = {"published"}
    _repr_ = "BaseVideo({0.videoId})"
    _infos_ = {"mediatype": "video"}
    _plot_ = localized_string(30056)
    _fields_ = {"title", "videoId", "videoThumbnails", "lengthSeconds", "author"}

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
            thumb=getattr(self.videoThumbnails, "sddefault", ""))

    def item(self, url, action):
        return self._item(build_url(url, action=action, videoId=self.videoId))


class ShortVideo(BaseVideo):

    _repr_ = "ShortVideo({0.videoId})"
    _plot_ = localized_string(30057)
    _fields_ = {"published", "viewCount"}


class Video(ShortVideo):

    _repr_ = "Video({0.videoId})"
    _plot_ = localized_string(30058)
    _live_ = localized_string(30059)
    _fields_ = {"description", "liveNow", "dashUrl", "hlsUrl"}

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
    _plot_ = localized_string(30060)
    _fields_ = {"author", "authorId", "autoGenerated", "description", "authorThumbnails"}

    def item(self, url, action):
        return ListItem(
            self.author,
            build_url(url, action=action, authorId=self.authorId),
            isFolder=True,
            infos={"video": {"plot": self.plot()}},
            poster=getattr(self.authorThumbnails, "512", ""))


# playlists --------------------------------------------------------------------

class Playlist(InvidiousItem):

    _repr_ = "Playlist({0.playlistId})"
    _plot_ = localized_string(30061)
    _fields_ = {"title", "playlistId", "playlistThumbnail", "videoCount", "videos", "authorId"}

    def item(self, url, action):
        return ListItem(
            self.title,
            build_url(url, action=action, playlistId=self.playlistId),
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

    def __init__(self, items, limit=0, page=0, content=None, category=None):
        super(InvidiousItems, self).__init__((self._ctor_(item) for item in items))
        self.more = (len(self) >= limit) if limit else False
        self.content = content or self._content_
        self.category = category or self._category_

    def items(self, *args):
        return (item.item(*args) for item in self if item)

    @classmethod
    def fields(cls):
        return getattr(cls, "_fields_", cls._ctor_.fields())


class Folders(InvidiousItems):

    _ctor_ = Folder


class Home(Folders):

    def __init__(self):
        super(Home, self).__init__(_home_folders_)


class BaseVideos(InvidiousItems):

    _ctor_ = BaseVideo


class ShortVideos(InvidiousItems):

    _ctor_ = ShortVideo


class Videos(InvidiousItems):

    _ctor_ = Video


class Channels(InvidiousItems):

    _ctor_ = Channel


class Playlists(InvidiousItems):

    _ctor_ = Playlist


class ChannelPlaylists(InvidiousItems):

    _ctor_ = Playlist
    _fields_ = {"playlists", "continuation"}

    def __init__(self, playlists, category=None, continuation=None):
        super(ChannelPlaylists, self).__init__(playlists, category=category)
        if continuation:
            self.more = True
            self.continuation = continuation

