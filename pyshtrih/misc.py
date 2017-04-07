# -*- coding: utf-8 -*-


import struct
import locale
import operator
import functools
import collections


LOCALE = locale.getpreferredencoding()
NULL = bytearray((0x00, ))

DEFAULT_MIN_LENGTH = 40
T_TAPES = collections.namedtuple('Tapes', ['control', 'cash', 'skid'])

BAUDRATE_DIRECT = {
    2400: 0,
    4800: 1,
    9600: 2,
    19200: 3,
    38400: 4,
    57600: 5,
    115200: 6
}
BAUDRATE_REVERSE = {v: k for k, v in BAUDRATE_DIRECT.items()}

TLV_LEN_MAX = 250


def bytearray_cast(arg):
    if not isinstance(arg, bytearray):
        return bytearray(arg)
    return arg


def bytearray_concat(*args):
    """
    Функция конкатенирования нескольких bytearray в один.
    """

    return bytearray_cast(reduce(operator.concat, args))


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
    Расчет контрольной суммы.
    """

    return reduce(operator.xor, buff)


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


def prepare_string(string, length=DEFAULT_MIN_LENGTH):
    """
    Подготовка строки к отправке в ККМ.

    :type string: unicode
    :param string: строка для передачи в ККМ
    :type length: int
    :param length: максимальная длина строки

    :rtype: bytearray
    :return: строка, готовая к передаче в ККМ
    """

    # нужно отправить в ККМ не менее DEFAULT_MIN_LENGTH символов
    if length < DEFAULT_MIN_LENGTH:
        length = DEFAULT_MIN_LENGTH

    if string:
        result = bytearray(encode(string)[:length])
        result.extend(NULL * (length - len(string)))
    else:
        result = NULL * length

    return result


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


def bits_to_int(bits, reverse=False):
    """
    Функция, возвращающая целое число из набора бит.

    >>> bits_to_int((0, 0, 0, 1, 1, 0, 1, 1))
    27
    >>> bits_to_int((0, 0, 0, 1, 1, 0, 1, 1), True)
    216
    >>> bits_to_int((0, 0, 0, 0, 0, 0, 0, 1))
    1
    >>> bits_to_int((0, 0, 0, 0, 0, 0, 0, 1), True)
    128
    >>> bits_to_int((1, 0, 0, 0, 0, 0, 0, 1))
    129
    >>> bits_to_int((1, 0, 0, 0, 0, 0, 0, 1), True)
    129

    :type bits: collections.Iterable
    :param bits: набор бит
    :type reverse: bool
    :param reverse: интерпретировать биты в обратном порядке

    :type: int
    :return: целое число
    """

    result = 0

    if reverse:
        bits = reversed(bits)

    for bit in bits:
        result = (result << 1) | bit

    return result


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


def chunks(source, num):
    """
    Функция нарезания списка на множество списков по заданному количеству элементов.

    >>> list(chunks([1, 0, 1, 1], 2)) == [[1, 0], [1, 1]]
    True

    :type source: collection.Iterable
    :param: source: исходный список
    :type num: int
    :param num: количество элементов

    :rtype: types.GeneratorType
    """

    for i in xrange(0, len(source), num):
        yield source[i:i + num]


def cast_byte_timeout(arg):
    """
    Приведение времени в секундах к коду таймаута.

    >>> cast_byte_timeout(0.0)
    0
    >>> cast_byte_timeout(0.15)
    150
    >>> cast_byte_timeout(0.30)
    151
    >>> cast_byte_timeout(15.0)
    249
    >>> cast_byte_timeout(30.0)
    250
    >>> cast_byte_timeout(105.0)
    255
    >>> cast_byte_timeout(0.16) # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: Неверное значение таймаута - 0.16 с.
    Значение должно соответсвовать одному из диапазонов: 0-0.15 с., 0.30-15 с., 30-105 с.
    >>> cast_byte_timeout(0.31) # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: Неверное значение таймаута - 0.31 с.
    Значение в диапазоне 0.30-15 с. должно быть кратно 0.15 с.
    >>> cast_byte_timeout(31.0) # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: Неверное значение таймаута - 31.0 с.
    Значение в диапазоне 30-105 с. должно быть кратно 15 с.

    :type arg: float
    :param arg: время в секундах

    :rtype: int
    :return: код таймаута
    """

    if 0.0 <= arg <= 0.15:
        return int(arg * 1000)
    elif 0.30 <= arg <= 15:
        div = arg / 0.15
        if not div.is_integer():
            raise ValueError(
                'Неверное значение таймаута - {} с. '
                'Значение в диапазоне 0.30-15 с. должно быть кратно 0.15 с.'.format(arg)
            )
        return int(div) + 149
    elif 30 <= arg <= 105:
        div = arg / 15
        if not div.is_integer():
            raise ValueError(
                'Неверное значение таймаута - {} с. '
                'Значение в диапазоне 30-105 с. должно быть кратно 15 с.'.format(arg)
            )
        return int(div) + 248
    else:
        raise ValueError(
            'Неверное значение таймаута - {} с. '
            'Значение должно соответсвовать одному из диапазонов: '
            '0-0.15 с., 0.30-15 с., 30-105 с.'.format(arg)
        )


class FuncChain(object):
    def __init__(self, *funcs):
        self.funcs = funcs

    def __call__(self, *args, **kwargs):
        if not self.funcs:
            return

        res = self.funcs[-1](*args, **kwargs)
        for func in reversed(self.funcs[:-1]):
            if res is None:
                break
            res = func(res)

        return res


fetchone = operator.itemgetter(0)


def unpack(fmt, string):
    """
    Функция, аналогичная функции struct.unpack, но возвращающая None в случае ошибки.
    """

    try:
        return struct.unpack(fmt, string)
    except struct.error:
        return


CMD_SIZE = {
    1: '>B',
    2: '>H'
}

CAST_CMD = {
    size: FuncChain(bytearray, functools.partial(struct.pack, fmt)) for size, fmt in CMD_SIZE.items()
}


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
    size: FuncChain(bytearray, functools.partial(struct.pack, fmt)) for size, fmt in CHAR_SIZE.items()
}

UNCAST_SIZE = {
    size: (
        FuncChain(fetchone, functools.partial(unpack, fmt))
        if len(size) == 1
        else functools.partial(struct.unpack, fmt)
    )
    for size, fmt in CHAR_SIZE.items()
}
