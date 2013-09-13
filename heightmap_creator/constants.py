# -*- coding: utf-8 -*-

import os

from twisted.python.constants import ValueConstant, Values


class SERVER_STATE(Values):
    BUSY = ValueConstant("busy")
    READY = ValueConstant("ready")


class RESPONSE(Values):
    DONE = ValueConstant("read")
    FAIL = ValueConstant("fail")


# 1:MAP_SCALE tells what distanse is represented in one pixel in on dimention
MAP_SCALE = 100

MAX_HEIGHT = 9000
MAX_OBJECTS_ON_MAP = 10000
MAX_TCP_BUFFER_SIZE = 900000

DS_CONSOLE_TIMEOUT = 30
DL_TIMEOUT = 10

MISSION_TEMPLATE = """[MAIN]
  MAP {:}
  TIME 12.0
  CloudType 0
  CloudHeight 1000.0
  army 1
  playerNum 0
[NStationary]
"""
