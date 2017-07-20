# -*- coding: utf-8 -*-


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

    name = device.Device.name


def discovery(callback=None, port=None, baudrate=None):
    """
    Функция автоопределения подключеннных устройств.

    :param callback: callable объект, принимающий 2 параметра: порт и скорость
    :type port: str
    :param port: порт взаимодействия с устройством
    :type baudrate: int
    :param baudrate: скорость взаимодействия с устройством

    :rtype: list
    :return: список экземпляров оборудования
    """

    devices = []

    if port and baudrate:
        ports = (port, )
        baudrates = (baudrate, )
    else:
        # явное приведение результата функции comports к типу list
        # необходимо для совместимости с pyserial <= 3.0.1 на платформе win32
        ports = (port_.device for port_ in reversed(list(serial.tools.list_ports.comports())))
        baudrates = sorted(misc.BAUDRATE_DIRECT.keys(), reverse=True)

    for p in ports:
        for b in baudrates:
            if callback:
                callback(p, b)

            try:
                d = Discovery(p, b)
            except IOError:
                pass
            else:
                device_cls = None

                if u'ФР-ПТК' in d.name:
                    device_cls = device.ShtrihFRPTK
                elif u'LIGHT-ПТК' in d.name:
                    device_cls = device.ShtrihLightPTK
                elif u'ПТК' in d.name:
                    device_cls = device.ShtrihComboPTK
                elif u'КОМБО-ФР-К' in d.name:
                    device_cls = device.ShtrihComboFRK
                elif u'ФР-К' in d.name:
                    device_cls = device.ShtrihFRK
                elif u'ФР-01Ф' in d.name:
                    device_cls = device.ShtrihFR01F
                elif u'950К' in d.name:
                    device_cls = device.Shtrih950K
                elif u'ON-LINE' in d.name:
                    device_cls = device.ShtrihOnLine
                elif u'РИТЕЙЛ-01Ф' in d.name:
                    device_cls = device.Retail01F
                elif u'М-01Ф' in d.name:
                    device_cls = device.ShtrihM01F
                elif u'ЛАЙТ-01Ф' in d.name:
                    device_cls = device.ShtrihLight01F
                elif u'МИНИ-01Ф' in d.name:
                    device_cls = device.ShtrihMini01F

                if device_cls:
                    discovered_device = device_cls(p, b)
                    discovered_device.dev_info = d.dev_info
                    devices.append(discovered_device)

                break

    return devices
