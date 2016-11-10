# -*- coding: utf-8 -*-


import serial.tools.list_ports

import commands
import protocol
import misc


class Discovery(object):
    __metaclass__ = commands.SupportedCommands
    SUPPORTED_COMMANDS = (0xFC, )
    DISCOVERY_TIMEOUT = 0.5

    def __init__(self, port, baudrate):
        self.protocol = protocol.Protocol(
            port, baudrate, self.DISCOVERY_TIMEOUT
        )
        self.protocol.connect()
        self.dev_info = self.model()
        self.protocol.disconnect()


def discovery():
    devices = {}

    for p in (port.device for port in serial.tools.list_ports.comports()):
        print p
        for b in sorted(misc.BAUDRATE_DIRECT.keys()):
            print b
            try:
                d = Discovery(p, b)
            except IOError:
                pass
            else:
                devices[p] = d.dev_info

    return devices

# def connect(self):
#     """
#     Метод подключения к устройству.
#     """
#
#     if not self.serial.isOpen():
#         connected = False
#
#         if self.port is None:
#             ports = tuple(p.device for p in serial.tools.list_ports.comports())
#         else:
#             ports = (self.port,)
#
#         if self.baudrate is None:
#             baudrates = tuple(BAUDRATE_DIRECT.keys())
#         else:
#             baudrates = (self.baudrate,)
#
#         for p in ports:
#             self.serial.port = p
#             if not self.serial.isOpen():
#                 try:
#                     self.serial.open()
#                 except serial.SerialException as exc:
#                     raise NoConnectionError(u'Нет связи с ККМ ({})'.format(exc))
#             print p
#             for b in sorted(baudrates):
#                 print b
#                 self.serial.baudrate = b
#                 if list(self.check())[-1]:
#                     self.port = p
#                     self.baudrate = b
#                     connected = True
#                     break
#             break
#
#         if not connected:
#             raise NoConnectionError(u'Нет связи с ККМ')
