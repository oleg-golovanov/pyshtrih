# -*- coding: utf-8 -*-


from . import protocol, commands, misc, compat
from .handlers import commands as hc, functions as hf


class Device(compat.with_metaclass(commands.SupportedCommands)):
    SERIAL_TIMEOUT = 3
    WAIT_TIME = 0.01

    DEFAULT_CASHIER_PASSWORD = 1
    DEFAULT_ADMIN_PASSWORD = 30

    DEFAULT_MAX_LENGTH = 40

    TAPES = misc.T_TAPES(False, False, False)
    FS = False

    def __init__(self, port='/dev/ttyS0', baudrate=9600, timeout=None, password=None, admin_password=None):
        """
        :type port: str
        :param port: порт взаимодействия с устройством
        :type baudrate: int
        :param baudrate: скорость взаимодействия с устройством
        :type timeout: float
        :param timeout: время таймаута ответа устройства
        :type password: int
        :param password: пароль кассира
        :type admin_password: int
        :param admin_password: пароль администратора
        """

        self.protocol = protocol.Protocol(
            port,
            baudrate,
            timeout or self.SERIAL_TIMEOUT,
            fs=self.FS
        )

        self.password = password or self.DEFAULT_CASHIER_PASSWORD
        self.admin_password = admin_password or self.DEFAULT_ADMIN_PASSWORD

        self.dev_info = None

    @property
    def port(self):
        return self.protocol.port

    @port.setter
    def port(self, port):
        self.protocol.port = port
        if self.connected:
            self.connect(force=True)

    @property
    def baudrate(self):
        return self.protocol.serial.baudrate

    @baudrate.setter
    def baudrate(self, baudrate):
        self.protocol.serial.baudrate = baudrate
        if self.connected:
            self.connect(force=True)

    @property
    def timeout(self):
        return self.protocol.serial.timeout

    @timeout.setter
    def timeout(self, timeout):
        self.protocol.serial.timeout = timeout
        self.protocol.serial.write_timeout = timeout

    @property
    def connected(self):
        """
        Флаг подключенности.

        :rtype: bool
        """

        return self.protocol.connected

    @property
    def name(self):
        """
        Название устройства.

        :rtype: unicode
        """

        return self.dev_info[u'Название устройства'] if self.dev_info else u''

    def connect(self, force=False):
        """
        Подключиться к ККМ.

        :type force: bool
        :param force: отключиться перед подключением
        """

        if force:
            self.protocol.disconnect()

        self.protocol.connect()

        if hasattr(self, 'model'):
            self.dev_info = self.model()
            hf.handle_fr_flags.model = self.dev_info[u'Модель устройства']

    def disconnect(self):
        """
        Отключиться от ККМ.
        """

        self.protocol.disconnect()


class ShtrihFRK(Device):
    SUPPORTED_COMMANDS = (
        0x10, 0x11, 0x13, 0x14, 0x15, 0x16, 0x17, 0x19, 0x1A, 0x1B, 0x1E, 0x1F, 0x21, 0x22, 0x23, 0x25, 0x28, 0x29,
        0x2B, 0x2D, 0x2E, 0x40, 0x41, 0x50, 0x51, 0x80, 0x82, 0x85, 0x86, 0x87, 0x88, 0x8C, 0x8D, 0xB0, 0xC2, 0xFC
    )

    DEFAULT_MAX_LENGTH = 36
    TAPES = misc.T_TAPES(True, True, False)


class ShtrihComboFRK(Device):
    SUPPORTED_COMMANDS = (
        0x10, 0x11, 0x13, 0x14, 0x15, 0x16, 0x17, 0x19, 0x1A, 0x1B, 0x1E, 0x1F, 0x21, 0x22, 0x23, 0x25, 0x28, 0x29,
        0x2B, 0x2D, 0x2E, 0x40, 0x41, 0x50, 0x51, 0x80, 0x82, 0x85, 0x86, 0x87, 0x88, 0x8C, 0x8D, 0xB0, 0xC0, 0xC1,
        0xC2, 0xE0, 0xFC
    )

    DEFAULT_MAX_LENGTH = 48
    TAPES = misc.T_TAPES(False, True, True)


class ShtrihLightPTK(Device):
    SUPPORTED_COMMANDS = (
        0x10, 0x11, 0x13, 0x14, 0x15, 0x16, 0x17, 0x19, 0x1A, 0x1B, 0x1E, 0x1F, 0x21, 0x22, 0x23, 0x25, 0x28, 0x29,
        0x2B, 0x2D, 0x2E, 0x40, 0x41, 0x50, 0x51, 0x80, 0x82, 0x85, 0x86, 0x87, 0x88, 0x8C, 0x8D, 0xB0, 0xC0, 0xC1,
        0xC2, 0xFC
    )

    DEFAULT_MAX_LENGTH = 36
    TAPES = misc.T_TAPES(False, True, False)


class Shtrih950K(Device):
    SUPPORTED_COMMANDS = (
        0x10, 0x11, 0x13, 0x14, 0x15, 0x16, 0x17, 0x19, 0x1A, 0x1B, 0x1E, 0x1F, 0x21, 0x22, 0x23, 0x25, 0x28, 0x29,
        0x2B, 0x2D, 0x2E, 0x40, 0x41, 0x50, 0x51, 0x80, 0x82, 0x85, 0x86, 0x87, 0x88, 0x8C, 0x8D, 0xB0, 0xFC
    )

    DEFAULT_MAX_LENGTH = 40
    TAPES = misc.T_TAPES(False, True, True)


class ShtrihFRPTK(ShtrihFRK):
    pass


class ShtrihComboPTK(ShtrihComboFRK):
    pass


class ShtrihFR01F(Device):
    SUPPORTED_COMMANDS = (
        0x10, 0x11, 0x13, 0x14, 0x15, 0x16, 0x17, 0x19, 0x1A, 0x1B, 0x1E, 0x1F, 0x21, 0x22, 0x23, 0x25, 0x28, 0x29,
        0x2B, 0x2D, 0x2E, 0x40, 0x41, 0x50, 0x51, 0x80, 0x82, 0x85, 0x86, 0x87, 0x88, 0x8C, 0x8D, 0xB0, 0xC0, 0xC1,
        0xC2, 0xE0, 0xFC, 0xFF01, 0xFF03, 0xFF08, 0xFF0A, 0xFF0C, 0xFF35, 0xFF36, 0xFF38, 0xFF39, 0xFF3F, 0xFF40,
        0xFF41, 0xFF42
    )

    DEFAULT_MAX_LENGTH = 36
    TAPES = misc.T_TAPES(False, True, False)
    FS = True


class ShtrihOnLine(ShtrihFR01F):
    pass


class ShtrihM01F(ShtrihFR01F):
    DEFAULT_MAX_LENGTH = 48


class ShtrihM02F(ShtrihFR01F):
    DEFAULT_MAX_LENGTH = 48


class ShtrihLight01F(ShtrihFR01F):
    DEFAULT_MAX_LENGTH = 32


class ShtrihLight02F(ShtrihFR01F):
    DEFAULT_MAX_LENGTH = 32


class ShtrihMini01F(ShtrihFR01F):
    DEFAULT_MAX_LENGTH = 50


class Retail01F(ShtrihFR01F):
    DEFAULT_MAX_LENGTH = 42


class ShtrihAllCommands(Device):
    SUPPORTED_COMMANDS = hc.COMMANDS.keys()
