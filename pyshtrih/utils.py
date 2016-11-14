# -*- coding: utf-8 -*-


import collections

import serial.tools.list_ports

import device
import commands
import protocol
import misc


class Discovery(object):
    __metaclass__ = commands.SupportedCommands
    SUPPORTED_COMMANDS = (0xFC, )
    DISCOVERY_TIMEOUT = 0.5

    def __init__(self, port, baudrate):
        """
        Псевдо-устройство, позволяющее определить тип подключенного оборудования.

        :type port: str
        :param port: порт взаимодействия с устройством
        :type baudrate: int
        :param baudrate: скорость взаимодействия с устройством
        """

        self.protocol = protocol.Protocol(
            port, baudrate, self.DISCOVERY_TIMEOUT
        )
        self.protocol.connect()
        self.dev_info = self.model()
        self.protocol.disconnect()


def discovery(callback=None):
    """
    Функция автоопределения подключеннных устройств.

    :param callback: callable объект, принимающий 2 параметра: порт и скорость

    :rtype: collections.OrderedDict
    :return: упорядоченый словарь пар порт - экземпляр класса оборудования
    """

    devices = collections.OrderedDict()

    for p in (port.device for port in reversed(serial.tools.list_ports.comports())):
        for b in sorted(misc.BAUDRATE_DIRECT.keys(), reverse=True):
            if callback:
                callback(p, b)

            try:
                d = Discovery(p, b)
            except IOError:
                pass
            else:
                model_name = d.dev_info[u'Название устройства']
                device_cls = None

                if u'ПТК' in model_name:
                    device_cls = device.ShtrihComboPTK
                elif u'КОМБО-ФР-К' in model_name:
                    device_cls = device.ShtrihComboFRK
                elif u'ФР-К' in model_name:
                    device_cls = device.ShtrihFRK

                if device_cls:
                    discovered_device = device_cls(p, b)
                    discovered_device.dev_info = d.dev_info
                    devices[p] = discovered_device

                break

    return devices
