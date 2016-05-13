# -*- coding: utf-8 -*-


import serial

from misc import lrc, bytearray_cast, bytearray_concat, CAST_SIZE, UNCAST_SIZE
from handlers import HANDLERS, ERROR_CODE_STR


STX = bytearray.fromhex('02')
ENQ = bytearray.fromhex('05')
ACK = bytearray.fromhex('06')  # положительное подтверждение
NAK = bytearray.fromhex('15')  # отрицательное подтверждение


class ProtocolError(IOError):
    pass


class NoConnectionError(ProtocolError):
    pass


class UnexpectedResponseError(ProtocolError):
    pass


class Error(ProtocolError):
    pass


class Protocol(object):
    MAX_ATTEMPTS = 10

    def __init__(self, port, baudrate, timeout):
        """
        Класс описывающий протокол взаимодействия в устройством.

        :type port: str
        :param port: порт взаимодействия с устройством
        :type baudrate: int
        :param baudrate: скорость взаимодействия с устройством
        :type timeout: int
        :param timeout: время таймаута ответа устройства
        """

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.serial = None

    def connect(self):
        """
        Метод подключения к устройству.
        """

        if not self.serial:
            self.serial = serial.Serial(
                self.port,
                self.baudrate,
                parity = serial.PARITY_NONE,
                stopbits = serial.STOPBITS_ONE,
                timeout = self.timeout,
                writeTimeout = self.timeout
            )
        if not self.serial.isOpen():
            try:
                self.serial.open()
            except serial.SerialException as exc:
                raise NoConnectionError(u'Нет связи с ККМ ({})'.format(exc))

    def disconnect(self):
        """
        Метод отключения от устройства.
        """

        if self.serial:
            self.serial.close()

    def init(self):
        """
        Метод инициализации устройства перед отправкой команды.
        """

        try:
            self.serial.write(ENQ)
            byte = self.serial.read()

            if byte == NAK:
                pass
            elif byte == ACK:
                self.handle_response()
            else:
                raise UnexpectedResponseError(u'Неизвестный ответ ККМ')

        except serial.writeTimeoutError:
            raise ProtocolError(u'Не удалось записать байт в ККМ')
        except serial.SerialException as exc:
            raise ProtocolError(unicode(exc))

    def handle_response(self):
        """
        Метод обработки ответа ККМ.

        :rtype: dict
        :return: ответ ККМ в виде словаря
        """

        for _ in xrange(self.MAX_ATTEMPTS):
            try:
                stx = self.serial.read()
                if stx != STX:
                    raise NoConnectionError(u'Нет связи с ККМ')

                length = self.serial.read()
                payload = self.serial.read(UNCAST_SIZE['1'](length))
                _lrc = UNCAST_SIZE['1'](self.serial.read())

                if lrc(bytearray_concat(length, payload)) == _lrc:
                    self.serial.write(ACK)
                    return self.handle_payload(payload)
                else:
                    self.serial.write(NAK)
                    self.serial.write(ENQ)
                    byte = self.serial.read()
                    if byte != ACK:
                        raise UnexpectedResponseError(u'Получен байт {}, ожидался ACK'.format(byte))

            except serial.SerialException as exc:
                raise ProtocolError(unicode(exc))
        else:
            raise NoConnectionError(u'Нет связи с ККМ')

    def handle_payload(self, payload):
        """
        Метод обработки полезной нагрузки ответа ККМ.

        :type payload: str or bytearray
        :param payload: часть ответа ККМ, содержащая полезную нагрузку

        :rtype: dict
        :return: набор параметров в виде словаря
        """

        payload = bytearray_cast(payload)

        try:
            cmd = payload[0]
        except IndexError:
            raise UnexpectedResponseError(u'Не удалось получить байт команды из ответа')

        response = payload[slice(1, None)]

        handler = HANDLERS.get(cmd)

        if handler:
            result = {
                name: func(response[_slice]) for _slice, func, name in handler
            }

            error = result.get(ERROR_CODE_STR, 0)
            if error != 0:
                raise Error(error)

            return result

        return response

    def command_nopass(self, cmd, params = bytearray()):
        """
        Метод отправки команды без пароля оператора.

        :type cmd: int
        :param cmd: номер команды
        :type params: bytearray
        :param params: набор параметров команды

        :rtype: dict
        :return: набор параметров ответа в виде словаря
        """

        if not isinstance (params, bytearray):
            raise TypeError(u'{} expected, got {} instead'.format(bytearray, type(params)))

        buff = bytearray_concat(
            CAST_SIZE['1'](1 + len(params)),
            CAST_SIZE['1'](cmd),
            params
        )
        command = bytearray_concat(STX, buff, CAST_SIZE['1'](lrc(buff)))

        self.init()
        for _ in xrange(self.MAX_ATTEMPTS):
            self.serial.write(command)
            byte = self.serial.read()
            if byte == ACK:
                return self.handle_response()
        else:
            raise NoConnectionError(u'Нет связи с ККМ')

    def command(self, cmd, password, *params):
        """
        Метод отправки команды с паролем оператора.

        :type cmd: int
        :param cmd: номер команды
        :type password: int
        :param password: пароль оператора
        :type params: bytearray
        :param params: набор параметров команды

        :rtype: dict
        :return: набор параметров ответа в виде словаря
        """

        params = bytearray_concat(
            CAST_SIZE['4'](password), *params
        )

        return self.command_nopass(cmd, params)


class Driver(object):
    SERIAL_TIMEOUT = 1

    DEFAULT_CASHIER_PASSWORD = 1
    DEFAULT_ADMIN_PASSWORD = 30

    DEFAULT_MAX_LENGTH = 48

    TABLES_COUNT = 15

    # TODO: подумать можно ли избавиться от port и baudrate в пользу автоматического поиска устройства
    def __init__(self, port = '/dev/ttyS0', baudrate = 9600, timeout = None, password = None, admin_password = None):
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

    def disconnect (self):
        """
        Отключиться от ККМ.
        """

        if not self.connected:
            return
        self.protocol.disconnect()
        self.connected = False

    def full_state (self):
        """
        Состояние ККМ.
        """
        return self.protocol.command(0x11, self.password)

    def cut(self, partial = False):
        """
        Обрезка чека.
        """
        return self.protocol.command(0x25, self.password, CAST_SIZE['1'](partial))

    def test_start(self, minute):
        """
        Тестовый прогон
        """
        return self.protocol.command (0x19, self.password, CAST_SIZE['1'](minute))

    def test_stop(self):
        """
        Прерывание тестового прогона
        """
        return self.protocol.command (0x2B, self.password)

    def model(self):
        return self.protocol.command_nopass(0xFC)

    # def checkout (self):
    #     '''
    #     Регистрация и печать чека
    #     '''
    #     raise NotImplementedError ('checkout() is not implemented')
    #
    # def open_shift (self):
    #     '''
    #     Открыть смену
    #     '''
    #     if self.shift_is_open ():
    #         raise RuntimeError (u'Смена уже открыта')
    #     self._do_open_shift ()
    #
    # def shift_is_open (self):
    #     raise NotImplementedError ('shift_is_open() is not implemented')
    #
    # def z_report (self):
    #     '''
    #     Z-отчет
    #     '''
    #     if not self.shift_is_open ():
    #         raise RuntimeError (u'Смена закрыта')
    #     self._do_z_report ()
    #
    # def x_report (self):
    #     '''
    #     X-отчет
    #     '''
    #     raise NotImplementedError ('x_report() is not implemented')
    #
    # def open_drawer (self):
    #     '''
    #     Открыть денежный ящик
    #     '''
    #     raise NotImplementedError ('open_drawer() is not implemented')
    #
    # def beep (self):
    #     '''
    #     Звуковой сигнал
    #     '''
    #     raise NotImplementedError ('beep() is not implemented')
    #
    # def income (self, sum):
    #     '''
    #     Инкассация
    #     '''
    #     if sum <= 0:
    #         raise RuntimeError (u'Сумма должна быть больше нуля')
    #     if not self.shift_is_open ():
    #         raise RuntimeError (u'Смена закрыта')
    #     self._do_income (sum)
    #
    # def outcome (self, sum):
    #     '''
    #     Пополнение
    #     '''
    #     if sum <= 0:
    #         raise RuntimeError (u'Сумма должна быть больше нуля')
    #     if not self.shift_is_open ():
    #         raise RuntimeError (u'Смена закрыта')
    #     self._do_outcome (sum)
    #
    # def continue_print (self):
    #     '''
    #     Продолжить печать после получения PrintError
    #     '''
    #     raise NotImplementedError ('continue_print() is not implemented')
    #
    # def cancel_check (self):
    #     raise NotImplementedError ('cancel_check() is not implemented')
    #
    # def storno (self):
    #     '''
    #     Сторнирование документа
    #     '''
    #     raise NotImplementedError ('storno() is not implemented')


if __name__ == '__main__':
    p = Driver()
    p.connect()
    # print(repr(p.command(0x13, p.DEFAULT_CASHIER_PASSWORD)).decode('unicode-escape'))
#    print(repr(p.test_start(1)).decode('unicode-escape'))
    print(repr(p.test_stop()).decode('unicode-escape'))
    # print(repr(p.command_nopass(0xFC)).decode('unicode-escape'))
