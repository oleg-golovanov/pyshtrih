# -*- coding: utf-8 -*-


import struct
from operator import concat, xor, itemgetter
from functools import partial
from datetime import date, time
from binascii import hexlify
from itertools import compress


def bytearray_cast(arg):
    if not isinstance(arg, bytearray):
        return bytearray(arg)
    return arg


def bytearray_concat(*args):
    """
    Функция конкатенирования нескольких bytearray в один.
    """
    return bytearray_cast(reduce(concat, args))


def lrc (buff):
    """
    Расчет контрольной суммы
    """

    return reduce(xor, buff)


def encode (text):
    """
    кодирование текста для передачи фискальному регистратору
    """
    return unicode (text).encode ('cp1251')


def decode (text):
    """
    декодирование текста полученного с фискального регистратора
    """
    return text.decode ('cp1251')


def int_to_bitmask(num, length=8):
    return map(int, ('{:0%sb}' % length).format(num))


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
            (u'Отказ правого датчика принтера', u'Бумага на входе в презентер')[revision],
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

    bitmask = int_to_bitmask(arg, 16)

    a, b = 0, 1
    flags_actual = {
        4: ((0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1), a),
        9: ((0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0), a)
    }

    flags, rev = flags_actual.get(
        handle_fr_flags.model,
        ((1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1), a)
    )

    return dict(
        zip(
            compress(get_keys(rev), flags),
            compress(bitmask, flags)
        )
    )
handle_fr_flags.model = -1


def handle_fp_flags(arg):
    keys = (u'ФП 1', u'ФП 2', u'Лицензия', u'Переполнение ФП',
            u'Батарея ФП', u'Последняя запись ФП', u'Смена в ФП', u'24 часа в ФП')
    bitmask = int_to_bitmask(arg, 8)

    return dict(zip(keys, bitmask))


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

CHAR_SIZE = {
    '1': '<B',
    '2': '<H',
    '4': '<I',
    '11': '<2B',
    '111': '<3B'
}

CAST_SIZE = {
    size: FuncChain(bytearray, partial(struct.pack, fmt)) for size, fmt in CHAR_SIZE.items()
}

UNCAST_SIZE = {
    size: FuncChain(fetchone, partial(struct.unpack, fmt)) if len(size) == 1 else partial(struct.unpack, fmt)
    for size, fmt in CHAR_SIZE.items()
}
