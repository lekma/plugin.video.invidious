# -*- coding: utf-8 -*-





import re
import math
import xml.etree.ElementTree as ET


# ------------------------------------------------------------------------------
# DashElement
# ------------------------------------------------------------------------------

class DashElement(ET.Element):

    @staticmethod
    def duration(arg):
        return "PT{:.1f}S".format(math.floor(float(arg) * 10)/10.0)

    @staticmethod
    def range(**kwargs):
        return "{start}-{end}".format(**kwargs)

    _defaults_ = {}

    def __init__(self, **kwargs):
        super(DashElement, self).__init__(
            self.__class__.__name__, attrib=self._defaults_, **kwargs
        )

    def toString(self):
        class dummy:
            pass
        data = []
        file = dummy()
        file.write = data.append
        ET.ElementTree(self).write(
            file, xml_declaration=True, encoding="utf-8", method="xml"
        )
        return "".join(data)


# ------------------------------------------------------------------------------
# Initialization
# ------------------------------------------------------------------------------

class Initialization(DashElement):

    def __init__(self, **initRange):
        super(Initialization, self).__init__(
            range=self.range(**initRange)
        )


# ------------------------------------------------------------------------------
# SegmentBase
# ------------------------------------------------------------------------------

class SegmentBase(DashElement):

    def __init__(self, indexRange, data):
        super(SegmentBase, self).__init__(
            indexRange=self.range(**indexRange)
        )
        initRange = data.get("initRange", {})
        if initRange:
            self.append(Initialization(**initRange))


# ------------------------------------------------------------------------------
# BaseURL
# ------------------------------------------------------------------------------

class BaseURL(DashElement):

    def __init__(self, url):
        super(BaseURL, self).__init__()
        self.text = url


# ------------------------------------------------------------------------------
# AudioChannelConfiguration
# ------------------------------------------------------------------------------

class AudioChannelConfiguration(DashElement):

    _defaults_ = {
        "schemeIdUri": "urn:mpeg:dash:23003:3:audio_channel_configuration:2011"
    }

    def __init__(self, audioChannels):
        super(AudioChannelConfiguration, self).__init__(
            value=str(audioChannels)
        )


# ------------------------------------------------------------------------------
# Representation
# ------------------------------------------------------------------------------

class Representation(DashElement):

    def __init__(self, data):
        kwargs = {
            "id": str(data["itag"]),
            "codecs": data["codecs"],
            "bandwidth": str(data["bitrate"])
        }
        # width
        width = data.get("width", 0)
        if width:
            kwargs["width"] = str(width)
        # height
        height = data.get("height", 0)
        if height:
            kwargs["height"] = str(height)
        # frameRate
        frameRate = data.get("fps", 0)
        if frameRate:
            kwargs["frameRate"] = str(frameRate)
        super(Representation, self).__init__(**kwargs)
        audioChannels = data.get("audioChannels", 0)
        if audioChannels:
            self.append(AudioChannelConfiguration(audioChannels))
        self.append(BaseURL(data["url"]))
        indexRange = data.get("indexRange", {})
        if indexRange:
            self.append(SegmentBase(indexRange, data))


# ------------------------------------------------------------------------------
# AdaptationSet
# ------------------------------------------------------------------------------

class AdaptationSet(DashElement):

    _defaults_ = {
        #"segmentAlignment": "true",
        #"startWithSAP": "1",
        #"subsegmentAlignment": "true",
        #"subsegmentStartsWithSAP": "1",
        #"bitstreamSwitching": "true"
    }

    def __init__(self, id, mimeType, data):
        super(AdaptationSet, self).__init__(
            id=id,
            mimeType=mimeType,
            contentType=mimeType.split("/")[0]
        )
        self.extend(Representation(d) for d in data)


# ------------------------------------------------------------------------------
# Period
# ------------------------------------------------------------------------------

class Period(DashElement):

    _defaults_ = {
        "start": "PT0.0S"
    }

    def __init__(self, duration, data):
        super(Period, self).__init__(
            duration=self.duration(duration)
        )
        self.extend(AdaptationSet(str(id), *item)
                    for id, item in enumerate(data.items()))


# ------------------------------------------------------------------------------
# MPD
# ------------------------------------------------------------------------------

class MPD(DashElement):

    _defaults_ = {
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


# ------------------------------------------------------------------------------
# adaptive
# ------------------------------------------------------------------------------

_mimeType_regex_ = re.compile(r"^.*(?=;)|(?<=codecs=['\"]).*(?=['\"])")

def adaptive(duration, streams):
    data = {}
    for stream in streams:
        mimeType, codecs = _mimeType_regex_.findall(stream["mimeType"])
        stream.setdefault("codecs", codecs)
        data.setdefault(mimeType, []).append(stream)
    return (MPD(duration, data).toString(), "video/vnd.mpeg.dash.mpd")

