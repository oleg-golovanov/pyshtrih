# -*- coding: utf-8 -*-


from protocol import Protocol
from handlers import COMMANDS
from commands import SupportedCommands
from misc import handle_fr_flags, T_TAPES


class Device(object):
    __metaclass__ = SupportedCommands

    SERIAL_TIMEOUT = 3
    WAIT_TIME = 0.01

    DEFAULT_CASHIER_PASSWORD = 1
    DEFAULT_ADMIN_PASSWORD = 30

    DEFAULT_MAX_LENGTH = 40

    TAPES = T_TAPES(False, False, False)

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

        self.protocol = Protocol(
            port,
            baudrate,
            timeout or self.SERIAL_TIMEOUT
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
            handle_fr_flags.model = self.dev_info[u'Модель устройства']

    def disconnect(self):
        """
        Отключиться от ККМ.
        """

        self.protocol.disconnect()


class ShtrihFRK(Device):
    SUPPORTED_COMMANDS = (
        0x10, 0x11, 0x13, 0x14, 0x15, 0x17, 0x19, 0x1A, 0x1B, 0x1E, 0x1F, 0x21, 0x22, 0x23, 0x25, 0x28, 0x29, 0x2B,
        0x2D, 0x2E, 0x40, 0x41, 0x50, 0x51, 0x80, 0x82, 0x85, 0x86, 0x87, 0x88, 0x8C, 0x8D, 0xB0, 0xC2, 0xFC
    )

    DEFAULT_MAX_LENGTH = 36
    TAPES = T_TAPES(True, True, False)


class ShtrihComboFRK(Device):
    SUPPORTED_COMMANDS = (
        0x10, 0x11, 0x13, 0x14, 0x15, 0x17, 0x19, 0x1A, 0x1B, 0x1E, 0x1F, 0x21, 0x22, 0x23, 0x25, 0x28, 0x29, 0x2B,
        0x2D, 0x2E, 0x40, 0x41, 0x50, 0x51, 0x80, 0x82, 0x85, 0x86, 0x87, 0x88, 0x8C, 0x8D, 0xB0, 0xC0, 0xC1, 0xC2,
        0xE0, 0xFC
    )

    DEFAULT_MAX_LENGTH = 48
    TAPES = T_TAPES(False, True, True)


ShtrihFRPTK = ShtrihFRK
ShtrihComboPTK = ShtrihComboFRK


class ShtrihAllCommands(Device):
    SUPPORTED_COMMANDS = COMMANDS.keys()
