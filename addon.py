# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals

import sys

from lib.dispatcher import dispatch


if __name__ == "__main__":
    dispatch(*sys.argv)

