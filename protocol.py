# -*- coding: utf-8 -*-


import serial

from misc import mslice, lrc, bytearray_cast, bytearray_concat, CAST_SIZE, UNCAST_SIZE
from handlers import HANDLERS, ERROR_CODE_STR
from excepts import ProtocolError, NoConnectionError, UnexpectedResponseError, Error


STX = bytearray.fromhex('02')
ENQ = bytearray.fromhex('05')
ACK = bytearray.fromhex('06')  # положительное подтверждение
NAK = bytearray.fromhex('15')  # отрицательное подтверждение


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
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                writeTimeout=self.timeout
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
            result = {}
            for _slice, func, name in handler:
                chunk = _slice(response) if isinstance(_slice, mslice) else response[_slice]
                if chunk and name is None:
                    result.update(func(chunk))
                elif chunk:
                    result[name] = func(chunk) if func else chunk
                else:
                    result[name] = None

            error = result.get(ERROR_CODE_STR, 0)
            if error != 0:
                raise Error(error)

            return result

        return response

    def command_nopass(self, cmd, params=bytearray()):
        """
        Метод отправки команды без пароля оператора.

        :type cmd: int
        :param cmd: номер команды
        :type params: bytearray
        :param params: набор параметров команды

        :rtype: dict
        :return: набор параметров ответа в виде словаря
        """

        if not isinstance(params, bytearray):
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
