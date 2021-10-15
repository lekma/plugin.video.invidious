# -*- coding: utf-8 -*-


import io
import math
import re
import xml.etree.ElementTree as ET


# ------------------------------------------------------------------------------
# DashElement

class DashElement(ET.Element):

    @staticmethod
    def duration(arg):
        return f"PT{(math.floor(float(arg) * 10)/10.0):.1f}S"

    @staticmethod
    def range(**kwargs):
        return "{start}-{end}".format(**kwargs)

    __defaults__ = {}

    def __init__(self, **kwargs):
        super(DashElement, self).__init__(
            self.__class__.__name__, attrib=self.__defaults__, **kwargs
        )

    def toString(self):
        with io.BytesIO() as stream:
            ET.ElementTree(self).write(
                stream, encoding="UTF-8", xml_declaration=True, method="xml"
            )
            return stream.getvalue()


# ------------------------------------------------------------------------------
# Initialization

class Initialization(DashElement):

    def __init__(self, **initRange):
        super(Initialization, self).__init__(range=self.range(**initRange))


# ------------------------------------------------------------------------------
# SegmentBase

class SegmentBase(DashElement):

    def __init__(self, indexRange, data):
        super(SegmentBase, self).__init__(indexRange=self.range(**indexRange))
        if (initRange := data.get("initRange", {})):
            self.append(Initialization(**initRange))


# ------------------------------------------------------------------------------
# BaseURL

class BaseURL(DashElement):

    def __init__(self, url):
        super(BaseURL, self).__init__()
        self.text = url


# ------------------------------------------------------------------------------
# AudioChannelConfiguration

class AudioChannelConfiguration(DashElement):

    __defaults__ = {
        "schemeIdUri": "urn:mpeg:dash:23003:3:audio_channel_configuration:2011"
    }

    def __init__(self, audioChannels):
        super(AudioChannelConfiguration, self).__init__(
            value=str(audioChannels)
        )


# ------------------------------------------------------------------------------
# Representation

class Representation(DashElement):

    def __init__(self, data):
        kwargs = {
            "id": str(data["itag"]),
            "codecs": data["codecs"],
            "bandwidth": str(data["bitrate"])
        }
        # width
        if (width := data.get("width", 0)):
            kwargs["width"] = str(width)
        # height
        if (height := data.get("height", 0)):
            kwargs["height"] = str(height)
        # frameRate
        if (frameRate := data.get("fps", 0)):
            kwargs["frameRate"] = str(frameRate)
        super(Representation, self).__init__(**kwargs)
        if (audioChannels := data.get("audioChannels", 0)):
            self.append(AudioChannelConfiguration(audioChannels))
        self.append(BaseURL(data["url"]))
        if (indexRange := data.get("indexRange", {})):
            self.append(SegmentBase(indexRange, data))


# ------------------------------------------------------------------------------
# AdaptationSet

class AdaptationSet(DashElement):

    __defaults__ = {
        #"segmentAlignment": "true",
        #"startWithSAP": "1",
        #"subsegmentAlignment": "true",
        #"subsegmentStartsWithSAP": "1",
        #"bitstreamSwitching": "true"
    }

    def __init__(self, id, mimeType, data):
        super(AdaptationSet, self).__init__(
            id=id, mimeType=mimeType, contentType=mimeType.split("/")[0]
        )
        self.extend(Representation(d) for d in data)


# ------------------------------------------------------------------------------
# Period

class Period(DashElement):

    __defaults__ = {
        "start": "PT0.0S"
    }

    def __init__(self, duration, data):
        super(Period, self).__init__(duration=self.duration(duration))
        self.extend(
            AdaptationSet(str(id), *item)
            for id, item in enumerate(data.items())
        )


# ------------------------------------------------------------------------------
# MPD

class MPD(DashElement):

    __defaults__ = {
        "xmlns": "urn:mpeg:dash:schema:mpd:2011",
        "profiles": "urn:mpeg:dash:profile:full:2011",
        "minBufferTime": "PT1.5S",
        #"type": "static"
    }

    def __init__(self, duration, data):
        super(MPD, self).__init__(
            mediaPresentationDuration=self.duration(duration)
        )
        self.append(Period(duration, data))


# adaptive ---------------------------------------------------------------------

__mimeType_regex__ = re.compile(r"^.*(?=;)|(?<=codecs=['\"]).*(?=['\"])")

def adaptive(duration, streams):
    data = {}
    for stream in streams:
        mimeType, codecs = __mimeType_regex__.findall(stream["mimeType"])
        stream.setdefault("codecs", codecs)
        data.setdefault(mimeType, []).append(stream)
    return (MPD(duration, data).toString(), "video/vnd.mpeg.dash.mpd")

