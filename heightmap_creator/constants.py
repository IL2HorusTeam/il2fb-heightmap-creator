# -*- coding: utf-8 -*-

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
MAX_OBJECTS_ON_MAP = 1000
