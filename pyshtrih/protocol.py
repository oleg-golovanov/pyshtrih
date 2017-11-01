# -*- coding: utf-8 -*-


import serial
import unilog

from . import misc, excepts
from .compat import unicode, xrange, str_compat
from .handlers import commands as hc


STX = bytearray((0x02, ))  # START OF TEXT - начало текста
ENQ = bytearray((0x05, ))  # ENQUIRY - запрос
ACK = bytearray((0x06, ))  # ACKNOWLEDGE - положительное подтверждение
NAK = bytearray((0x15, ))  # NEGATIVE ACKNOWLEDGE - отрицательное подтверждение


class Protocol(object):
    MAX_ATTEMPTS = 10
    CHECK_NUM = 3

    def __init__(self, port, baudrate, timeout, fs=False):
        """
        Класс описывающий протокол взаимодействия в устройством.

        :type port: str
        :param port: порт взаимодействия с устройством
        :type baudrate: int
        :param baudrate: скорость взаимодействия с устройством
        :type timeout: float
        :param timeout: время таймаута ответа устройства
        :type fs: bool
        :param fs: признак наличия ФН (фискальный накопитель)
        """

        self.port = port
        self.serial = serial.Serial(
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
            writeTimeout=timeout
        )
        self.fs = fs
        self.connected = False

    def connect(self):
        """
        Метод подключения к устройству.
        """

        if not self.connected:
            self.serial.port = self.port
            if not self.serial.isOpen():
                try:
                    self.serial.open()
                except serial.SerialException as exc:
                    raise excepts.NoConnectionError(
                        u'Не удалось открыть порт {} ({})'.format(
                            self.port, exc
                        )
                    )

            for r in self.check(self.CHECK_NUM, True):
                if r:
                    self.connected = True
                    return
            else:
                self.serial.close()
                raise excepts.NoConnectionError()

    def disconnect(self):
        """
        Метод отключения от устройства.
        """

        if self.connected:
            self.serial.close()
            self.connected = False

    def init(self):
        """
        Метод инициализации устройства перед отправкой команды.
        """

        try:
            self.serial.write(ENQ)
            byte = self.serial.read()
            if not byte:
                raise excepts.NoConnectionError()

            if byte == NAK:
                pass
            elif byte == ACK:
                self.handle_response()
            else:
                while self.serial.read():
                    pass
                return False

            return True

        except serial.SerialTimeoutException:
            self.serial.flushOutput()
            raise excepts.ProtocolError(u'Не удалось записать байт в ККМ')
        except serial.SerialException as exc:
            self.serial.flushInput()
            raise excepts.ProtocolError(unicode(exc))

    def handle_response(self):
        """
        Метод обработки ответа ККМ.

        :rtype: dict
        :return: ответ ККМ в виде словаря
        """

        for _ in xrange(self.MAX_ATTEMPTS):
            stx = self.serial.read()
            if stx != STX:
                raise excepts.NoConnectionError()

            length = self.serial.read()
            payload = self.serial.read(misc.UNCAST_SIZE['1'](length))
            _lrc = misc.UNCAST_SIZE['1'](self.serial.read())

            if misc.lrc(misc.bytearray_concat(length, payload)) == _lrc:
                self.serial.write(ACK)
                return self.handle_payload(payload)
            else:
                self.serial.write(NAK)
                self.serial.write(ENQ)
                byte = self.serial.read()
                if byte != ACK:
                    raise excepts.UnexpectedResponseError(u'Получен байт 0x{:02X}, ожидался ACK'.format(ord(byte)))
        else:
            raise excepts.NoConnectionError()

    def handle_payload(self, payload):
        """
        Метод обработки полезной нагрузки ответа ККМ.

        :type payload: str or bytearray
        :param payload: часть ответа ККМ, содержащая полезную нагрузку

        :rtype: dict
        :return: набор параметров в виде словаря
        """

        payload = misc.bytearray_cast(payload)

        # предполагаем, что команда однобайтная
        cmd_len = 1
        try:
            cmd = payload[0]
            # если байт полный, то скорее всего команда двубайтная,
            # т.к. в спецификации Штриха не предусмотрено команды с кодом 0xFF
            if cmd == 0xFF:
                cmd_len = 2
                cmd = misc.bytes_to_int((payload[1], cmd))
        except IndexError:
            raise excepts.UnexpectedResponseError(u'Не удалось получить байт(ы) команды из ответа')

        response = payload[slice(cmd_len, None)]
        handler = hc.HANDLERS.get(cmd)

        if handler:
            result = {}
            for _slice, func, name in handler:
                chunk = _slice(response) if isinstance(_slice, misc.mslice) else response[_slice]
                if chunk and name is None:
                    result.update(func(chunk))
                elif chunk:
                    result[name] = func(chunk) if func else chunk
                else:
                    result[name] = None

            error = result.get(hc.ERROR_CODE_STR, 0)
            if error != 0:
                raise excepts.Error(cmd, error, fs=self.fs)

            return Response(cmd, result)

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

        cmd_len = len(misc.int_to_bytes(cmd))
        buff = misc.bytearray_concat(
            misc.CAST_SIZE['1'](cmd_len + len(params)),
            misc.CAST_CMD[cmd_len](cmd),
            params
        )
        command = misc.bytearray_concat(STX, buff, misc.CAST_SIZE['1'](misc.lrc(buff)))

        for r in self.check(self.CHECK_NUM):
            if not r:
                continue

            for _ in xrange(self.MAX_ATTEMPTS):
                try:
                    self.serial.write(command)
                    byte = self.serial.read()
                    if byte == ACK:
                        return self.handle_response()

                except serial.SerialTimeoutException:
                    self.serial.flushOutput()
                    raise excepts.ProtocolError(u'Не удалось записать байт в ККМ')
                except serial.SerialException as exc:
                    self.serial.flushInput()
                    raise excepts.ProtocolError(unicode(exc))
            else:
                raise excepts.NoConnectionError()
        else:
            raise excepts.NoConnectionError()

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

        params = misc.bytearray_concat(
            misc.CAST_SIZE['4'](password), *params
        )

        return self.command_nopass(cmd, params)

    def check(self, count=1, quiet=False):
        """
        Проверка связи с ККМ.

        :type count: int
        :param count: количество отправляемых пакетов
        :type quiet: bool
        :param quiet: подавление исключений
        """

        if self.serial is None:
            raise excepts.ProtocolError(u'Необходимо вначале выполнить метод connect()')

        if count < 1:
            raise ValueError('Параметр count должен быть >= 1')

        for _ in xrange(count):
            try:
                yield self.init()
            except excepts.NoConnectionError:
                if quiet:
                    yield False
                else:
                    raise


@str_compat
class Response(object):
    __slots__ = (
        'cmd',
        'cmd_name',
        'params'
    )

    def __init__(self, cmd, params):
        """
        Класс ответа ККМ.

        :type cmd: int
        :param cmd: номер команды
        :type params: dict
        :param params: словарь параметров ответа ККМ
        """

        self.cmd = cmd
        self.cmd_name = hc.COMMANDS[cmd]
        self.params = params

    def __getitem__(self, item):
        return self.params[item]

    def __setitem__(self, key, value):
        self.params[key] = value

    def __str__(self):
        return u'0x{:02X} ({}) - {}'.format(
            self.cmd,
            self.cmd_name,
            unilog.as_unicode(self.params)
        )

    __repr__ = __str__
