# -*- coding: utf-8 -*-

from twisted.python.constants import ValueConstant, Values


class SERVER_STATE(Values):
    BUSY = ValueConstant("busy")
    READY = ValueConstant("ready")
