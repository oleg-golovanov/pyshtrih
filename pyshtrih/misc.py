# -*- coding: utf-8 -*-


import struct
import locale
from operator import concat, xor, itemgetter
from functools import partial
from datetime import date, time
from binascii import hexlify
from itertools import compress
from collections import namedtuple


LOCALE = locale.getpreferredencoding()
NULL = bytearray((0, ))

T_TAPES = namedtuple('Tapes', ['control', 'cash', 'skid'])


def dict_pprint(arg):
    """
    Функция преобразования словаря в строку.

    :type arg: dict
    :param arg: словарь

    :rtype: str
    :return: строка
    """

    if not isinstance(arg, dict):
        raise TypeError('ожидается тип dict, {} получен'.format(type(arg).__name__))

    format_map = {
        dict: dict_pprint,
        unicode: lambda x: "'{}'".format(x.encode(LOCALE)),
        str: lambda x: "'{}'".format(x)
    }

    result = []

    for k, v in arg.items():
        k = format_map.get(type(k), lambda x: x)(k)

        result.append('{}: {}'.format(
            k,
            format_map.get(type(v), lambda x: x)(v))
        )

    return '{{{}}}'.format(', '.join(result))


def bytearray_cast(arg):
    if not isinstance(arg, bytearray):
        return bytearray(arg)
    return arg


def bytearray_concat(*args):
    """
    Функция конкатенирования нескольких bytearray в один.
    """

    return bytearray_cast(reduce(concat, args))


def bytearray_strip(arg):
    """
    Функция отрезания нулевых байт от набора байт.
    """

    return arg.strip(NULL)


class mslice(object):
    def __init__(self, *args):
        """
        Класс множественных срезов.

        :param args: набор объектов класса slice
        """

        if not all(map(lambda i: isinstance(i, slice), args)):
            raise TypeError('support only slice objects')

        self.slices = args

    def __call__(self, arg):
        """
        Вызов.

        :type arg: bytearray
        :param arg: нарезаемый объект

        :rtype: bytearray
        :return: нарезанный объект
        """

        return bytearray_concat(*(arg[s] for s in self.slices))


def lrc(buff):
    """
    Расчет контрольной суммы
    """

    return reduce(xor, buff)


def encode(text):
    """
    Кодирование текста для передачи фискальному регистратору.
    """

    return text.encode('cp1251')


def decode(text):
    """
    Декодирование текста полученного с фискального регистратора.
    """

    return text.decode('cp1251')


def int_to_bits(num, length=None):
    """
    Функция, возвращающая битовое представление заданного числа.

    :type num: int
    :param num: целое число
    :type length: int
    :param length: количество бит, если указано, то число будет урезано до указанной длины

    :rtype: tuple
    :return: битовое представление числа
    """

    if not length:
        length = num.bit_length()

    result = [(num >> (1 * i) & 0x01) for i in xrange(length)]
    result.reverse()

    return tuple(result)


def int_to_bytes(num, count=None):
    """
    Функция преобрабования целого числа в набор байт.

    :type num: int or long
    :param num: число
    :type count: int
    :param count: количество байт, если указано, то число будет усечено до
                  указанного количества байт

    :rtype: tuple
    :return: набор байт
    """

    if count:
        bytes_count = count
    else:
        if num == 0:
            bytes_count = 1
        else:
            q, r = divmod(num.bit_length(), 8)
            bytes_count = q + 1 if r else q

    return tuple((num >> (8 * i)) & 0xff for i in xrange(bytes_count))


def bytes_to_int(arg):
    """
    Функция преобразования набора байт в целое число.

    :type arg: list or tuple ot bytearray
    :param arg: набор байт

    :rtype: int
    :return: целое число
    """

    return sum(b << (8 * i) for i, b in enumerate(arg))


def handle_version(arg):
    return '.'.join(map(chr, arg))


def handle_date(arg):
    d, m, y = arg
    return date(2000 + y, m, d)


def handle_time(arg):
    return time(*arg)


def handle_fr_flags(arg):
    def get_keys(revision):
        return (
            (u'Увеличенная точность количества', u'Буфер принтера непуст')[revision],
            u'ЭКЛЗ почти заполнена',
            (u'Отказ левого датчика принтера', u'Бумага на выходе из презентера')[revision],
            (u'Отказ правого датчика принтера', u'Бумага на входе в презентер', u'Модель принтера')[revision],
            u'Денежный ящик',
            u'Крышка корпуса ФР',
            u'Рычаг термоголовки чековой ленты',
            u'Рычаг термоголовки контрольной ленты',
            u'Оптический датчик чековой ленты',
            u'Оптический датчик операционного журнала',
            u'ЭКЛЗ',
            u'Положение десятичной точки',
            u'Нижний датчик подкладного документа',
            u'Верхний датчик подкладного документа',
            u'Рулон чековой ленты',
            u'Рулон операционного журнала'
        )

    bits = int_to_bits(arg, 16)

    a, b, c = 0, 1, 2
    flags_actual = {
        # ШТРИХ-ФР-К
        4: ((0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1), a),
        # ШТРИХ-КОМБО-ФР-К
        9: ((0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0), a),
        # ШТРИХ-КОМБО-ФР-К (версия 02)
        12: ((0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0), a)
    }

    flags, rev = flags_actual.get(
        handle_fr_flags.model,
        ((1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1), a)
    )

    return dict(
        zip(
            compress(get_keys(rev), flags),
            compress(bits, flags)
        )
    )
handle_fr_flags.model = -1


def handle_baudrate(arg):
    """
    Функция обработки значения скорости обмена.
    """

    return {
        0: 2400,
        1: 4800,
        2: 9600,
        3: 19200,
        4: 38400,
        5: 57600,
        6: 115200
    }.get(arg, 0)


def handle_byte_timeout(arg):
    """
    Функция обработки тайм аута приема байта.
    """

    if 0 <= arg <= 150:
        return arg
    elif 151 <= arg <= 249:
        return (arg - 149) * 150
    elif 250 <= arg <= 255:
        return (arg - 248) * 15000
    else:
        return -1


def handle_type_field(arg):
    """
    Функция обработки типа поля таблицы.
    """

    return {
        0: int,
        1: str
    }[arg]


def handle_min_max_field_value(arg):
    """
    Функция обработки минимального и максимального значения для команды
    0x2E "Запрос структуры поля".
    """

    result = {}

    bytes_count = UNCAST_SIZE['1'](arg[slice(0, 1)])
    result[u'Количество байт'] = bytes_count
    result[u'Минимальное значение поля'] = bytes_to_int(
        arg[slice(1, bytes_count + 1)]
    )
    result[u'Максимальное значение поля'] = bytes_to_int(
        arg[slice(bytes_count + 1, bytes_count * 2 + 1)]
    )

    return result


class FRMode(object):
    MODE_DESCR = {
        0: u'Принтер в рабочем режиме.',
        1: u'Выдача данных.',
        2: u'Открытая смена, 24 часа не кончились.',
        3: u'Открытая смена, 24 часа кончились.',
        4: u'Закрытая смена.',
        5: u'Блокировка по неправильному паролю налогового инспектора.',
        6: u'Ожидание подтверждения ввода даты.',
        7: u'Разрешение изменения положения десятичной точки.',
        8: u'Открытый документ:',
        9: u'Режим разрешения технологического обнуления.',
        10: u'Тестовый прогон.',
        11: u'Печать полного фис. отчета.',
        12: u'Печать отчёта ЭКЛЗ.',
        13: u'Работа с фискальным подкладным документом:',
        14: u'Печать подкладного документа:',
        15: u'Фискальный подкладной документ сформирован.'
    }
    MODE_STATUS = {
        8: {
            0: u'Продажа.',
            1: u'Покупка.',
            2: u'Возврат продажи.',
            3: u'Возврат покупки.'
        },
        13: {
            0: u'Продажа (открыт).',
            1: u'Покупка (открыт).',
            2: u'Возврат продажи (открыт).',
            3: u'Возврат покупки (открыт).'
        },
        14: {
            0: u'Ожидание загрузки.',
            1: u'Загрузка и позиционирование.',
            2: u'Позиционирование.',
            3: u'Печать.',
            4: u'Печать закончена.',
            5: u'Выброс документа.',
            6: u'Ожидание извлечения.',
        }
    }

    def __init__(self, code):
        self.num = code & 0x0f
        self.status = code >> 4

        if self.num not in self.MODE_STATUS:
            self.msg = self.MODE_DESCR[self.num]
        else:
            self.msg = u'{} {}'.format(
                self.MODE_DESCR[self.num],
                self.MODE_STATUS[self.num][self.status]
            )

    @property
    def state(self):
        return self.num, self.status

    def __str__(self):
        return self.msg.encode(LOCALE)

    def __unicode__(self):
        return self.msg

    __repr__ = __str__


class FRSubMode(object):
    SUBMODE_DESCR = {
        0: u'Бумага есть.',
        1: u'Нет бумаги.',
        2: u'ФР ждет бумагу для продолжения печати.',
        3: u'ФР ждет команду продолжения печати.',
        4: u'Печать фискальных отчетов.',
        5: u'Печать операции.'
    }

    def __init__(self, code):
        self.num = code
        self.msg = self.SUBMODE_DESCR[self.num]

    @property
    def state(self):
        return self.num

    def __str__(self):
        return self.msg.encode(LOCALE)

    def __unicode__(self):
        return self.msg

    __repr__ = __str__


def handle_fp_flags(arg):
    keys = (u'ФП 1', u'ФП 2', u'Лицензия', u'Переполнение ФП',
            u'Батарея ФП', u'Последняя запись ФП', u'Смена в ФП', u'24 часа в ФП')
    bits = int_to_bits(arg, 8)

    return dict(zip(keys, bits))


def handle_inn(arg):
    inn = hexlify(arg)

    if inn == 'ffffffffffff':
        return -1
    return int(inn, base=16)


class FuncChain(object):
    def __init__(self, *funcs):
        self.funcs = funcs

    def __call__(self, *args, **kwargs):
        if not self.funcs:
            return

        res = self.funcs[-1](*args, **kwargs)
        for func in reversed(self.funcs[:-1]):
            res = func(res)

        return res


fetchone = itemgetter(0)


def unpack(fmt, string):
    """
    Функция, аналогичная функции struct.unpack, но возвращающая None в случае ошибки.
    """

    try:
        return struct.unpack(fmt, string)
    except struct.error:
        return


CHAR_SIZE = {
    '1': '<B',
    '2': '<H',
    's2': '<h',
    '4': '<I',
    '11': '<2B',
    '111': '<3B',
    '1111': '<4B',
    '11111': '<5B',
    '121': '<BHB'
}

CAST_SIZE = {
    size: FuncChain(bytearray, partial(struct.pack, fmt)) for size, fmt in CHAR_SIZE.items()
}

UNCAST_SIZE = {
    size: FuncChain(fetchone, partial(unpack, fmt)) if len(size) == 1 else partial(struct.unpack, fmt)
    for size, fmt in CHAR_SIZE.items()
}
