# -*- coding: utf-8 -*-


import sys
import time
import inspect

import excepts
from misc import encode, decode, bytearray_strip, int_to_bytes, bytes_to_int, cast_byte_timeout, \
   prepare_string, FuncChain, BAUDRATE_DIRECT, CAST_SIZE


def state(self):
    """
    Состояние ККМ в коротком виде.
    """

    return self.protocol.command(0x10, self.password)
state.cmd = 0x10


def full_state(self):
    """
    Состояние ККМ.
    """

    return self.protocol.command(0x11, self.password)
full_state.cmd = 0x11


def beep(self):
    """
    Гудок.
    """

    return self.protocol.command(0x13, self.password)
beep.cmd = 0x13


def set_exchange_params(self, port, baudrate, timeout):
    """
    Установка параметров обмена.
    """

    return self.protocol.command(
        0x14,
        self.admin_password,
        CAST_SIZE['1'](port),
        CAST_SIZE['1'](BAUDRATE_DIRECT[baudrate]),
        CAST_SIZE['1'](cast_byte_timeout(timeout))
    )
set_exchange_params.cmd = 0x14


def read_exchange_params(self, port):
    """
    Чтение параметров обмена.
    """

    return self.protocol.command(0x15, self.admin_password, CAST_SIZE['1'](port))
read_exchange_params.cmd = 0x15


def print_string(self, string, control_tape=True, cash_tape=True):
    """
    Печать строки.
    """

    control = 0b01 if control_tape else 0b00
    cash = 0b10 if cash_tape else 0b00

    self.wait_printing()
    return self.protocol.command(
        0x17,
        self.password,
        CAST_SIZE['1'](control + cash),
        prepare_string(string, self.DEFAULT_MAX_LENGTH)
    )
print_string.cmd = 0x17


def print_line(self, symbol='-', control_tape=True, cash_tape=True):
    """
    Печать строки-разделителя.
    """

    return self.print_string(symbol * self.DEFAULT_MAX_LENGTH, control_tape, cash_tape)
print_string.related = (print_line, )


def test_start(self, minute):
    """
    Тестовый прогон.
    """

    self.wait_printing()
    return self.protocol.command(0x19, self.password, CAST_SIZE['1'](minute))
test_start.cmd = 0x19


def request_monetary_register(self, num):
    """
    Запрос денежного регистра.
    """

    return self.protocol.command(0x1A, self.password, CAST_SIZE['1'](num))
request_monetary_register.cmd = 0x1A


def request_operational_register(self, num):
    """
    Запрос операционного регистра.
    """

    return self.protocol.command(0x1B, self.password, CAST_SIZE['1'](num))
request_operational_register.cmd = 0x1B


def write_table(self, table, row, field, value, _type):
    """
    Запись таблицы.
    """

    cast_funcs_map = {
        int: FuncChain(bytearray, int_to_bytes),
        str: encode
    }

    return self.protocol.command(
        0x1E,
        self.admin_password,
        CAST_SIZE['121'](table, row, field),
        cast_funcs_map[_type](value)
    )
write_table.cmd = 0x1E


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
read_table.cmd = 0x1F


def set_time(self, time_):
    """
    Программирование времени.
    """

    # TODO: разобраться с округлением секунд до 00
    return self.protocol.command(
        0x21, self.admin_password, CAST_SIZE['111'](time_.hour, time_.minute, time_.second)
    )
set_time.cmd = 0x21


def set_date(self, date):
    """
    Программирование даты.
    """

    return self.protocol.command(
        0x22, self.admin_password, CAST_SIZE['111'](date.day, date.month, date.year - 2000)
    )
set_date.cmd = 0x22


def confirm_date(self, date):
    """
    Подтверждение программирование даты.
    """

    return self.protocol.command(
        0x23, self.admin_password, CAST_SIZE['111'](date.day, date.month, date.year - 2000)
    )
confirm_date.cmd = 0x23


def set_datetime(self, datetime):
    """
    Установка даты и времени.
    """

    self.set_time(datetime.time())
    self.set_date(datetime.date())
    self.confirm_date(datetime.date())
set_time.related = (set_datetime, )
set_date.related = (set_datetime, )
confirm_date.related = (set_datetime, )
set_datetime.required = (set_time, set_date, confirm_date)


def cut(self, partial=False):
    """
    Обрезка чека.
    """

    self.wait_printing()
    return self.protocol.command(0x25, self.password, CAST_SIZE['1'](partial))
cut.cmd = 0x25


def open_drawer(self, box=0):
    """
    Открыть денежный ящик.
    """

    return self.protocol.command(0x28, self.password, CAST_SIZE['1'](box))
open_drawer.cmd = 0x28


def feed(self, count, control_tape=False, cash_tape=False, skid_document=False):
    """
    Протяжка чековой ленты на заданное количество строк.
    """

    if count > 255:
        raise ValueError(u'Количество строк должно быть меньше 255')

    control = 0b001 if control_tape else 0b000
    cash = 0b010 if cash_tape else 0b000
    skid = 0b100 if skid_document else 0b000

    self.wait_printing()
    return self.protocol.command(
        0x29, self.password, CAST_SIZE['1'](control + cash + skid), CAST_SIZE['1'](count)
    )
feed.cmd = 0x29


def test_stop(self):
    """
    Прерывание тестового прогона.
    """

    self.wait_printing()
    return self.protocol.command(0x2B, self.password)
test_stop.cmd = 0x2B


def request_table_structure(self, table):
    """
    Запрос структуры таблицы.
    """

    return self.protocol.command(0x2D, self.admin_password, CAST_SIZE['1'](table))
request_table_structure.cmd = 0x2D


def request_field_structure(self, table, field):
    """
    Запрос структуры поля.
    """

    return self.protocol.command(0x2E, self.admin_password, CAST_SIZE['11'](table, field))
request_field_structure.cmd = 0x2E


def x_report(self):
    """
    Суточный отчет без гашения.
    """

    self.wait_printing()
    return self.protocol.command(0x40, self.admin_password)
x_report.cmd = 0x40


def z_report(self):
    """
    Суточный отчет с гашением.
    """

    self.wait_printing()
    return self.protocol.command(0x41, self.admin_password)
z_report.cmd = 0x41


def income(self, cash):
    """
    Внесение.
    """

    self.wait_printing()
    return self.protocol.command(
        0x50,
        self.password,
        CAST_SIZE['11111'](*int_to_bytes(cash, 5))
    )
income.cmd = 0x50


def outcome(self, cash):
    """
    Выплата.
    """

    self.wait_printing()
    return self.protocol.command(
        0x51,
        self.password,
        CAST_SIZE['11111'](*int_to_bytes(cash, 5))
    )
outcome.cmd = 0x51


def sale(self, item, department_num=0, tax1=0, tax2=0, tax3=0, tax4=0):
    """
    Продажа.
    """

    text, quantity, price = item

    try:
        return self.protocol.command(
            0x80,
            self.password,
            CAST_SIZE['11111'](*int_to_bytes(quantity, 5)),
            CAST_SIZE['11111'](*int_to_bytes(price, 5)),
            CAST_SIZE['1'](department_num),
            CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
            prepare_string(text, self.DEFAULT_MAX_LENGTH)
        )
    except excepts.Error as exc:
        raise excepts.ItemSaleError(exc)
sale.cmd = 0x80


def return_sale(self, item, department_num=0, tax1=0, tax2=0, tax3=0, tax4=0):
    """
    Возврат продажи.
    """

    text, quantity, price = item

    return self.protocol.command(
        0x82,
        self.password,
        CAST_SIZE['11111'](*int_to_bytes(quantity, 5)),
        CAST_SIZE['11111'](*int_to_bytes(price, 5)),
        CAST_SIZE['1'](department_num),
        CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
        prepare_string(text, self.DEFAULT_MAX_LENGTH)
    )
return_sale.cmd = 0x82


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

    try:
        return self.protocol.command(
            0x85,
            self.password,
            CAST_SIZE['11111'](*int_to_bytes(cash, 5)),
            CAST_SIZE['11111'](*int_to_bytes(payment_type2, 5)),
            CAST_SIZE['11111'](*int_to_bytes(payment_type3, 5)),
            CAST_SIZE['11111'](*int_to_bytes(payment_type4, 5)),
            # TODO: проверить скидку/надбавку
            CAST_SIZE['s2'](discount_allowance),
            CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
            prepare_string(text, self.DEFAULT_MAX_LENGTH)
        )
    except excepts.ProtocolError as exc:
        raise excepts.CloseCheckError(exc)
close_check.cmd = 0x85


def discount(self, sum_, tax1=0, tax2=0, tax3=0, tax4=0, text=None):
    """
    Скидка.
    """

    return self.protocol.command(
        0x86,
        self.password,
        CAST_SIZE['11111'](*int_to_bytes(sum_, 5)),
        CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
        prepare_string(text, self.DEFAULT_MAX_LENGTH)
    )
discount.cmd = 0x86


def allowance(self, sum_, tax1=0, tax2=0, tax3=0, tax4=0, text=None):
    """
    Надбавка.
    """

    return self.protocol.command(
        0x87,
        self.password,
        CAST_SIZE['11111'](*int_to_bytes(sum_, 5)),
        CAST_SIZE['1111'](tax1, tax2, tax3, tax4),
        prepare_string(text, self.DEFAULT_MAX_LENGTH)
    )
allowance.cmd = 0x87


def cancel_check(self):
    """
    Аннулирование чека.
    """

    self.wait_printing()
    return self.protocol.command(0x88, self.password)
cancel_check.cmd = 0x88


def repeat(self):
    """
    Повтор документа.
    """

    self.wait_printing()
    return self.protocol.command(0x8C, self.password)
repeat.cmd = 0x8C


def open_check(self, check_type):
    """
    Открыть чек.
    """

    self.wait_printing()
    try:
        return self.protocol.command(0x8D, self.password, CAST_SIZE['1'](check_type))
    except excepts.Error as exc:
        raise excepts.OpenCheckError(exc)
open_check.cmd = 0x8D


def continue_print(self):
    """
    Продолжение печати.
    """

    return self.protocol.command(0xB0, self.admin_password)
continue_print.cmd = 0xB0


def load_graphics(self, line_num, *args):
    """
    Загрузка графики.
    """

    return self.protocol.command(0xC0, self.password, CAST_SIZE['1'](line_num), *args)
load_graphics.cmd = 0xC0


def print_graphics(self, start_line, end_line):
    """
    Печать графики.
    """

    self.wait_printing()
    return self.protocol.command(
        0xC1,
        self.password,
        CAST_SIZE['1'](start_line),
        CAST_SIZE['1'](end_line)
    )
print_graphics.cmd = 0xC1


def print_barcode(self, num):
    """
    Печать штрих-кода
    """

    self.wait_printing()
    return self.protocol.command(
        0xC2, self.password, CAST_SIZE['11111'](*int_to_bytes(num, 5))
    )
print_barcode.cmd = 0xC2


def open_shift(self):
    """
    Открыть смену.
    """

    return self.protocol.command(0xE0, self.password)
open_shift.cmd = 0xE0


def model(self):
    """
    Получить тип устройства.
    """

    return self.protocol.command_nopass(0xFC)
model.cmd = 0xFC


def wait_printing(self):
    """
    Метод ожидания окончания печати документа.
    """

    while True:
        time.sleep(self.WAIT_TIME)
        submode = self.state()[u'Подрежим ФР']

        if submode.state == 0:
            return
        if submode.state == 3:
            self.continue_print()
print_string.depends = (wait_printing, )
test_start.depends = (wait_printing, )
cut.depends = (wait_printing, )
feed.depends = (wait_printing, )
test_stop.depends = (wait_printing, )
x_report.depends = (wait_printing, )
z_report.depends = (wait_printing, )
income.depends = (wait_printing, )
outcome.depends = (wait_printing, )
cancel_check.depends = (wait_printing, )
repeat.depends = (wait_printing, )
open_check.depends = (wait_printing, )
print_graphics.depends = (wait_printing, )
print_barcode.depends = (wait_printing, )


module = sys.modules[__name__]
FUNCTIONS = {
    function.cmd if hasattr(function, 'cmd') else name: function
    for name, function in inspect.getmembers(module, inspect.isfunction)
    if function.__module__ == module.__name__
}


class SupportedCommands(type):
    def __new__(mcs, classname, supers, attributedict):
        command_nums = attributedict.get('SUPPORTED_COMMANDS', ())

        def relative_gen(cmd):
            if hasattr(cmd, 'depends'):
                for dpc in cmd.depends:
                    relative_gen(dpc)
                    if dpc not in attributedict.values():
                        yield dpc

            if hasattr(cmd, 'required'):
                if all(rqc in attributedict.values() for rqc in cmd.required):
                    yield cmd

            if hasattr(cmd, 'related'):
                for rlc in cmd.related:
                    relative_gen(rlc)
                    if rlc not in attributedict.values():
                        yield rlc

        for cn in command_nums:
            command = FUNCTIONS[cn]
            attributedict[command.__name__] = command

            for c in relative_gen(command):
                attributedict[c.__name__] = c

        return super(SupportedCommands, mcs).__new__(mcs, classname, supers, attributedict)
