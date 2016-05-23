# -*- coding: utf-8 -*-


from time import sleep

import serial

from misc import mslice, lrc, bytearray_cast, bytearray_concat, encode, int_to_bytes, \
    CAST_SIZE, UNCAST_SIZE
from handlers import HANDLERS, ERROR_CODE_STR
from exceptions import ProtocolError, NoConnectionError, UnexpectedResponseError, Error


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
                if chunk:
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


class Driver(object):
    SERIAL_TIMEOUT = 1
    WAIT_TIME = 0.01

    DEFAULT_CASHIER_PASSWORD = 1
    DEFAULT_ADMIN_PASSWORD = 30

    DEFAULT_MAX_LENGTH = 48

    TABLES_COUNT = 15

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

    def state(self):
        """
        Состояние ККМ в коротком виде.
        """

        return self.protocol.command(0x10, self.password)

    def full_state(self):
        """
        Состояние ККМ.
        """

        return self.protocol.command(0x11, self.password)

    def print_string(self, string, control_tape=True, cash_tape=True):
        """
        Печать строки.
        """

        control = 0b01 if control_tape else 0b00
        cash = 0b10 if cash_tape else 0b00

        result = self.protocol.command(
            0x17, self.password, CAST_SIZE['1'](control + cash), encode(string[:self.DEFAULT_MAX_LENGTH])
        )
        self.wait_printing()

        return result

    def print_line(self, symbol='-', control_tape=True, cash_tape=True):
        """
        Печать строки-разделителя.
        """

        return self.print_string(symbol * self.DEFAULT_MAX_LENGTH, control_tape, cash_tape)

    def test_start(self, minute):
        """
        Тестовый прогон.
        """

        return self.protocol.command(0x19, self.password, CAST_SIZE['1'](minute))

    def set_time(self, time):
        """
        Программирование времени.
        """

        # TODO: разобраться с округлением секунд до 00
        return self.protocol.command(
            0x21, self.admin_password, CAST_SIZE['111'](time.hour, time.minute, time.second)
        )

    def set_date(self, date):
        """
        Программирование даты.
        """

        return self.protocol.command(
            0x22, self.admin_password, CAST_SIZE['111'](date.day, date.month, date.year - 2000)
        )

    def confirm_date(self, date):
        """
        Подтверждение программирование даты.
        """

        return self.protocol.command(
            0x23, self.admin_password, CAST_SIZE['111'](date.day, date.month, date.year - 2000)
        )

    def set_datetime(self, datetime):
        """
        Установка даты и времени.
        """

        self.set_time(datetime.time())
        self.set_date(datetime.date())
        self.confirm_date(datetime.date())

    def cut(self, partial=False):
        """
        Обрезка чека.
        """

        return self.protocol.command(0x25, self.password, CAST_SIZE['1'](partial))

    def open_drawer(self, box=0):
        """
        Открыть денежный ящик.
        """

        return self.protocol.command(0x28, self.password, CAST_SIZE['1'](box))

    def feed(self, count, control_tape=False, cash_tape=False, skid_document=False):
        """
        Протяжка чековой ленты на заданное количество строк.
        """

        if count > 255:
            raise ValueError(u'Количество строк должно быть меньше 255')

        control = 0b001 if control_tape else 0b000
        cash = 0b010 if cash_tape else 0b000
        skid = 0b100 if skid_document else 0b000

        return self.protocol.command(
            0x29, self.password, CAST_SIZE['1'](control + cash + skid), CAST_SIZE['1'](count)
        )

    def test_stop(self):
        """
        Прерывание тестового прогона.
        """

        return self.protocol.command(0x2B, self.password)

    def x_report(self):
        """
        Суточный отчет без гашения.
        """

        result = self.protocol.command(0x40, self.admin_password)
        self.wait_printing()

        return result

    def z_report(self):
        """
        Суточный отчет с гашением.
        """

        result = self.protocol.command(0x41, self.admin_password)
        self.wait_printing()

        return result

    def income(self, cash):
        """
        Внесение.
        """

        result = self.protocol.command(
            0x50,
            self.password,
            CAST_SIZE['11111'](*int_to_bytes(cash, 5))
        )
        self.wait_printing()

        return result

    def outcome(self, cash):
        """
        Выплата.
        """

        result = self.protocol.command(
            0x51,
            self.password,
            CAST_SIZE['11111'](*int_to_bytes(cash, 5))
        )
        self.wait_printing()

        return result

    def sale(self, item, department_num=0, tax1=0, tax2=0, tax3=0, tax4=0):
        """
        Продажа.
        """

        text, quantity, price = item

        if text:
            text = bytearray(encode(text)[:40])
            text.extend((0, ) * (40 - len(text)))

        return self.protocol.command(
            0x80,
            self.password,
            CAST_SIZE['11111'](*int_to_bytes(quantity, 5)),
            CAST_SIZE['11111'](*int_to_bytes(price, 5)),
            CAST_SIZE['1'](department_num),
            CAST_SIZE['1'](tax1),
            CAST_SIZE['1'](tax2),
            CAST_SIZE['1'](tax3),
            CAST_SIZE['1'](tax4),
            text or bytearray((0, ) * 40)
        )

    def return_sale(self, item, department_num=0, tax1=0, tax2=0, tax3=0, tax4=0):
        """
        Возврат продажи.
        """

        text, quantity, price = item

        if text:
            text = bytearray(encode(text)[:40])
            text.extend((0, ) * (40 - len(text)))

        return self.protocol.command(
            0x82,
            self.password,
            CAST_SIZE['11111'](*int_to_bytes(quantity, 5)),
            CAST_SIZE['11111'](*int_to_bytes(price, 5)),
            CAST_SIZE['1'](department_num),
            CAST_SIZE['1'](tax1),
            CAST_SIZE['1'](tax2),
            CAST_SIZE['1'](tax3),
            CAST_SIZE['1'](tax4),
            text or bytearray((0, ) * 40)
        )

    def close_check(self,
                    cash=0,
                    payment_type2=0,
                    payment_type3=0,
                    payment_type4=0,
                    discount_allowance=0,
                    tax1=0,
                    tax2=0,
                    tax3=0,
                    tax4=0,
                    text=None):
        """
        Закрытие чека.
        """

        if text:
            text = bytearray(encode(text)[:40])
            text.extend((0, ) * (40 - len(text)))

        result = self.protocol.command(
            0x85,
            self.password,
            CAST_SIZE['11111'](*int_to_bytes(cash, 5)),
            CAST_SIZE['11111'](*int_to_bytes(payment_type2, 5)),
            CAST_SIZE['11111'](*int_to_bytes(payment_type3, 5)),
            CAST_SIZE['11111'](*int_to_bytes(payment_type4, 5)),
            # TODO: проверить скидку/надбавку
            CAST_SIZE['s2'](discount_allowance),
            CAST_SIZE['1'](tax1),
            CAST_SIZE['1'](tax2),
            CAST_SIZE['1'](tax3),
            CAST_SIZE['1'](tax4),
            text or bytearray((0, ) * 40)
        )
        self.wait_printing()

        return result

    def discount(self, sum_, tax1=0, tax2=0, tax3=0, tax4=0, text=None):
        """
        Скидка.
        """

        if text:
            text = bytearray(encode(text)[:40])
            text.extend((0, ) * (40 - len(text)))

        return self.protocol.command(
            0x86,
            self.password,
            CAST_SIZE['11111'](*int_to_bytes(sum_, 5)),
            CAST_SIZE['1'](tax1),
            CAST_SIZE['1'](tax2),
            CAST_SIZE['1'](tax3),
            CAST_SIZE['1'](tax4),
            text or bytearray((0, ) * 40)
        )

    def allowance(self, sum_, tax1=0, tax2=0, tax3=0, tax4=0, text=None):
        """
        Надбавка.
        """

        if text:
            text = bytearray(encode(text)[:40])
            text.extend((0, ) * (40 - len(text)))

        return self.protocol.command(
            0x87,
            self.password,
            CAST_SIZE['11111'](*int_to_bytes(sum_, 5)),
            CAST_SIZE['1'](tax1),
            CAST_SIZE['1'](tax2),
            CAST_SIZE['1'](tax3),
            CAST_SIZE['1'](tax4),
            text or bytearray((0, ) * 40)
        )

    def cancel_check(self):
        """
        Аннулирование чека.
        """

        # TODO: аннулирование чека с паролем администратора?
        return self.protocol.command(0x88, self.password)

    def repeat(self):
        """
        Повтор документа.
        """

        result = self.protocol.command(0x8C, self.password)
        self.wait_printing()

        return result

    def open_check(self, check_type):
        """
        Открыть чек.
        """

        return self.protocol.command(0x8D, self.password, CAST_SIZE['1'](check_type))

    def continue_print(self):
        """
        Продолжение печати.
        """

        result = self.protocol.command(0xB0, self.admin_password)
        self.wait_printing()

        return result

    def print_barcode(self, num):
        """
        Печать штрих-кода
        """

        result = self.protocol.command(
            0xC2, self.password, CAST_SIZE['11111'](*int_to_bytes(num, 5))
        )
        self.wait_printing()

        return result

    def open_shift(self):
        """
        Открыть смену.
        """

        return self.protocol.command(0xE0, self.password)

    def model(self):
        return self.protocol.command_nopass(0xFC)

    def wait_printing(self):
        """
        Метод ожидания окончания печати документа.
        """

        while True:
            sleep(self.WAIT_TIME)
            submode = self.state()[u'Подрежим ФР']

            if submode.state == 0:
                return
            if submode.state == 3:
                self.continue_print()

    # def checkout (self):
    #     '''
    #     Регистрация и печать чека
    #     '''
    #     raise NotImplementedError ('checkout() is not implemented')
    #
    # def shift_is_open (self):
    #     raise NotImplementedError ('shift_is_open() is not implemented')
