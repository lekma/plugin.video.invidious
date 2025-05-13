# -*- coding: utf-8 -*-


from datetime import date
from time import time

from nuttig import localizedString, Logger


# ------------------------------------------------------------------------------

def __date__(datestamp):
    if isinstance(datestamp, int):
        return date.fromtimestamp(datestamp)
    return datestamp


def __url__(url):
    return f"https:{url}" if url.startswith("//") else url


class Thumbnails(object):

    def __new__(cls, thumbnails=None):
        return super(Thumbnails, cls).__new__(cls) if thumbnails else None

    def __getattribute__(self, name):
        return __url__(super(Thumbnails, self).__getattribute__(name))


class Dict(dict):

    def __new__(cls, item):
        if item is not None:
            return super(Dict, cls).__new__(cls)
        return item


# ------------------------------------------------------------------------------
# IVVideo

class VideoThumbnails(Thumbnails):

    def __init__(self, thumbnails):
        if isinstance(thumbnails[0], list):
            thumbnails = thumbnails[0]
        for thumbnail in thumbnails:
            if isinstance(thumbnail, list):
                thumbnail = thumbnail[0]
            setattr(self, thumbnail["quality"], thumbnail["url"])


class IVVideo(Dict):

    def __init__(self, item, expires=1800):
        duration = (
            -1 if (live := item.get("liveNow", False))
            else item["lengthSeconds"]
            #else item.get("lengthSeconds", -1)
        )
        manifestType = "hls"
        mimeType = None
        if ((not live) or (not (url := item.get("hlsUrl")))):
            url = item.get("dashUrl")
            manifestType = "mpd"
            mimeType = "application/dash+xml"
        thumbnails = VideoThumbnails(item.get("videoThumbnails"))
        # published
        published, publishedText = (
            item.get("published", 0), item.get("publishedText")
        )
        if published:
            published = f"{__date__(published)}"
            publishedText = (
                f"{publishedText} ({published})" if publishedText else published
            )
        if publishedText:
            publishedText = localizedString(50101).format(publishedText)
        # views
        views, viewsText = item.get("viewCount", 0), item.get("viewCountText")
        if not viewsText and views:
            viewsText = localizedString(50102).format(views)
        # likes
        likes, likesText = item.get("likeCount", 0), item.get("likeCountText")
        if not likesText and likes:
            likesText = localizedString(50103).format(likes)
        super(IVVideo, self).__init__(
            type="video",
            videoId=item["videoId"],
            title=item["title"],
            description=(item.get("description") or None),
            channelId=item["authorId"],
            channel=item["author"],
            duration=duration,
            live=live,
            url=url,
            manifestType=manifestType,
            mimeType=mimeType,
            thumbnail=getattr(thumbnails, "high", None),
            published=published,
            publishedText=publishedText,
            views=views,
            viewsText=viewsText,
            likes=likes,
            likesText=likesText,
            language=item.get("language")
        )
        self.__expires__ = (int(time()) + expires)


# ------------------------------------------------------------------------------
# IVVideos

class IVVideos(list):

    def __init__(self, videos):
        super(IVVideos, self).__init__(
            IVVideo(video) for video in videos if video
        )


# ------------------------------------------------------------------------------
# YtDlpVideo

class YtDlpVideo(Dict):

    def __init__(self, item):
        # published
        if ((published := item.get("timestamp")) is not None):
            publishedText = localizedString(50101).format(__date__(published))
        else:
            publishedText = None
        # views
        if ((views := item.get("view_count")) is not None):
            viewsText = localizedString(50102).format(views)
        else:
            viewsText = None
        # likes
        if ((likes := item.get("like_count")) is not None):
            likesText = localizedString(50103).format(likes)
        else:
            likesText = None
        super(YtDlpVideo, self).__init__(
            type="video",
            videoId=item["video_id"],
            title=item["title"],
            description=(item.get("description") or None),
            channelId=item["channel_id"],
            channel=item["channel"],
            duration=item["duration"],
            live=item["is_live"],
            url=item["url"],
            manifestType=item["manifestType"],
            mimeType=item["mimeType"],
            thumbnail=item["thumbnail"],
            published=published,
            publishedText=publishedText,
            views=views,
            viewsText=viewsText,
            likes=likes,
            likesText=likesText,
            language=item.get("language")
        )


# ------------------------------------------------------------------------------
# IVPlaylist

class IVPlaylist(Dict):

    def __init__(self, item, expires=1800):
        thumbnail = (
            __url__(url) if (url := item.get("playlistThumbnail")) else None
        )
        # views
        views, viewsText = item.get("viewCount", 0), item.get("viewCountText")
        if not viewsText and views:
            viewsText = localizedString(50102).format(views)
        # videos
        videos, videosText = (
            item.get("videoCount", 0), item.get("videoCountText")
        )
        if not videosText and videos:
            videosText = localizedString(50301).format(videos)
        # updated
        updated, updatedText = (
            item.get("updated", 0), item.get("updatedText")
        )
        if updated:
            updated = f"{__date__(updated)}"
            updatedText = (
                f"{updatedText} ({updated})" if updatedText else updated
            )
        if updatedText:
            updatedText = localizedString(50302).format(updatedText)
        super(IVPlaylist, self).__init__(
            type="playlist",
            playlistId=item["playlistId"],
            title=item["title"],
            description=(item.get("description") or None),
            channelId=item["authorId"],
            channel=item["author"],
            thumbnail=thumbnail,
            views=views,
            viewsText=viewsText,
            videos=videos,
            videosText=videosText,
            updated=updated,
            updatedText=updatedText
        )
        self.__expires__ = (int(time()) + expires)


# ------------------------------------------------------------------------------
# IVPlaylists

class IVPlaylists(list):

    def __init__(self, playlists):
        super(IVPlaylists, self).__init__(
            IVPlaylist(playlist) for playlist in playlists if playlist
        )


# ------------------------------------------------------------------------------
# IVChannel

class ChannelThumbnails(Thumbnails):

    def __init__(self, thumbnails):
        for thumbnail in thumbnails:
            setattr(self, str(thumbnail["height"]), thumbnail["url"])


class IVChannel(Dict):

    __tabs__ = {
        "playlists": {"title": 31100},
        "streams": {"title": 31200},
        "shorts": {"title": 31300}
    }

    def __init__(self, item, expires=1800):
        thumbnails = ChannelThumbnails(item.get("authorThumbnails"))
        # subscribers
        subscribers, subscribersText = (
            item.get("subCount", 0), item.get("subCountText")
        )
        if not subscribersText and subscribers:
            subscribersText = localizedString(50201).format(subscribers)
        super(IVChannel, self).__init__(
            type="channel",
            channelId=item["authorId"],
            channel=item["author"],
            description=(item.get("description") or None),
            thumbnail=getattr(thumbnails, "512", None),
            subscribers=subscribers,
            subscribersText=subscribersText,
            tabs=[
                dict(tab, action=action, properties={"SpecialSort": "top"})
                for action, tab in self.__tabs__.items()
                if action in item.get("tabs", [])
            ]
        )
        self.__expires__ = (int(time()) + expires)

    def __repr__(self):
        return f"IVChannel({self['channel']})"


# ------------------------------------------------------------------------------
# IVResults

class IVResults(list):

    __types__ = {
        "video": IVVideo,
        "channel": IVChannel,
        "playlist": IVPlaylist
    }

    def __init__(self, items):
        super(IVResults, self).__init__(
            self.__types__[item["type"]](item) for item in items if item
        )
