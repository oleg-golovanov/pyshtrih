# -*- coding: utf-8 -*-


from time import sleep

from protocol import Protocol
from misc import encode, decode, bytearray_strip, int_to_bytes, bytes_to_int, FuncChain, CAST_SIZE


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

    def write_table(self, table, row, field, value, _type):
        # TODO: реализовать после реализации команды 2E "Запрос структуры поля"
        pass

    def read_table(self, table, row, field, _type):
        """
        Чтение таблицы.
        """

        cast_funcs_map = {
            int: bytes_to_int,
            str: FuncChain(decode, bytearray_strip)
        }

        if _type not in (cast_funcs_map.keys()):
            raise ValueError(
                u'ожидаемые типы {}'.format(', '.join(cast_funcs_map.keys()))
            )

        result = self.protocol.command(
            0x1F,
            self.admin_password,
            CAST_SIZE['121'](table, row, field)
        )
        result[u'Значение'] = cast_funcs_map[_type](result[u'Значение'])

        return result

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

    def request_table_structure(self, table):
        """
        Запрос структуры таблицы.
        """

        return self.protocol.command(0x2D, self.admin_password, CAST_SIZE['1'](table))

    def request_field_structure(self, table, field):
        """
        Запрос структуры поля.
        """

        return self.protocol.command(0x2E, self.admin_password, CAST_SIZE['11'](table, field))

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
            CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
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
            CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
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
            CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
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
            CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
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
            CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
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
