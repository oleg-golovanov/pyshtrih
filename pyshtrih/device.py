# -*- coding: utf-8 -*-


from protocol import Protocol


class Device(object):
    SERIAL_TIMEOUT = 3
    WAIT_TIME = 0.01

    DEFAULT_CASHIER_PASSWORD = 1
    DEFAULT_ADMIN_PASSWORD = 30

    DEFAULT_MAX_LENGTH = 40

    CONTROL_TAPE = False
    CASH_TAPE = False

    # TODO: подумать можно ли избавиться от port и baudrate в пользу автоматического поиска устройства
    def __init__(self, port='/dev/ttyS0', baudrate=9600, timeout=None, password=None, admin_password=None):
        """
        :type port: str
        :param port: порт взаимодействия с устройством
        :type baudrate: int
        :param baudrate: скорость взаимодействия с устройством
        :type timeout: int
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

        self.connected = False

    def connect(self):
        """
        Подключиться к ККМ.
        """

        if self.connected:
            self.disconnect()
        self.protocol.connect()
        self.connected = True

    def disconnect(self):
        """
        Отключиться от ККМ.
        """

        if not self.connected:
            return
        self.protocol.disconnect()
        self.connected = False


class ShtrihFRK(Device):
    CONTROL_TAPE = True
    CASH_TAPE = True
    DEFAULT_MAX_LENGTH = 36


class ShtrihComboFRK(Device):
    CASH_TAPE = True
    DEFAULT_MAX_LENGTH = 48


ShtrihComboPTK = ShtrihComboFRK
