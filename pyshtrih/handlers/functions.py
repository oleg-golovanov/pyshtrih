# -*- coding: utf-8 -*-


import datetime
import binascii
import itertools

from .. import misc
from ..compat import PY2, str_compat


def handle_version(arg):
    return '.'.join(map(chr, arg))


def handle_date(arg):
    d, m, y = arg
    return datetime.date(2000 + y, m, d)


def handle_revdate(arg):
    try:
        res = datetime.date(arg[0] + 2000, *arg[1:])
    except ValueError:
        res = datetime.date.fromtimestamp(0)

    return res


def handle_time(arg):
    return datetime.time(*arg)


def handle_datetime(arg):
    try:
        res = datetime.datetime(arg[0] + 2000, *arg[1:])
    except ValueError:
        res = datetime.datetime.fromtimestamp(0)

    return res


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

    bits = misc.int_to_bits(arg, 16)

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
            itertools.compress(get_keys(rev), flags),
            itertools.compress(bits, flags)
        )
    )
handle_fr_flags.model = -1


def handle_baudrate(arg):
    """
    Функция обработки значения скорости обмена.
    """

    return misc.BAUDRATE_REVERSE.get(arg, 0)


def handle_byte_timeout(arg):
    """
    Функция обработки тайм аута приема байта.

    :type arg: int
    :param arg: код таймаута

    :rtype: float
    :return: время в секундах
    """

    if 0 <= arg <= 150:
        return arg * 0.001
    elif 151 <= arg <= 249:
        return (arg - 149) * 0.15
    elif 250 <= arg <= 255:
        return (arg - 248) * 15.0
    else:
        return -1


def handle_type_field(arg):
    """
    Функция обработки типа поля таблицы.
    """

    values = {
        0: int,
        1: str
    }

    return values[arg]


def handle_min_max_field_value(arg):
    """
    Функция обработки минимального и максимального значения для команды
    0x2E "Запрос структуры поля".
    """

    result = {}

    bytes_count = misc.UNCAST_SIZE['1'](arg[slice(0, 1)])
    result[u'Количество байт'] = bytes_count
    result[u'Минимальное значение поля'] = misc.bytes_to_int(
        arg[slice(1, bytes_count + 1)]
    )
    result[u'Максимальное значение поля'] = misc.bytes_to_int(
        arg[slice(bytes_count + 1, bytes_count * 2 + 1)]
    )

    return result


@str_compat
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
        8: u'Открытый документ.',
        9: u'Режим разрешения технологического обнуления.',
        10: u'Тестовый прогон.',
        11: u'Печать полного фискального отчета.',
        12: u'Печать отчёта ЭКЛЗ.',
        13: u'Работа с фискальным подкладным документом.',
        14: u'Печать подкладного документа.',
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

        self.msg = self.MODE_DESCR.get(self.num, u'Неизвестный режим.')
        if self.num in self.MODE_STATUS:
            self.msg = u'{} {}'.format(
                self.msg.replace(u'.', u':'),
                self.MODE_STATUS[self.num].get(self.status, u'Неизвестный статус режима.')
            )

    @property
    def state(self):
        return self.num, self.status

    def __str__(self):
        return self.msg

    __repr__ = __str__


@str_compat
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
        return self.msg

    __repr__ = __str__


def handle_fp_flags(arg):
    keys = (u'ФП 1', u'ФП 2', u'Лицензия', u'Переполнение ФП',
            u'Батарея ФП', u'Последняя запись ФП', u'Смена в ФП', u'24 часа в ФП')
    bits = misc.int_to_bits(arg, 8)

    return dict(zip(keys, bits))


def handle_inn(arg):
    inn = binascii.hexlify(arg)
    if not PY2:
        inn = inn.decode()

    if inn == 'ffffffffffff':
        return -1
    return int(inn, base=16)


def handle_fs_lifestate(arg):
    values = (
        u'Закончена передача фискальных данных в ОФД',
        u'Закрыт фискальный режим',
        u'Открыт фискальный режим',
        u'Проведена настройка ФН'
    )

    return dict(zip(values, misc.int_to_bits(arg, 4)))


def handle_fs_current_document(arg):
    values = {
        0x00: u'нет открытого документа',
        0x01: u'отчет о фискализации',
        0x02: u'отчет об открытии смены',
        0x04: u'кассовый чек',
        0x08: u'отчет о закрытии смены',
        0x10: u'отчет о закрытии фискального режима',
        0x11: u'бланк строкой отчетности',
        0x12: u'отчет об изменении параметров регистрации ККТ в связи с заменой ФН',
        0x13: u'отчет об изменении параметров регистрации ККТ',
        0x14: u'кассовый чек коррекции',
        0x15: u'БСО коррекции',
        0x17: u'отчет о текущем состоянии расчетов'
    }

    return values.get(arg, u'неизвестный тип документа')


def handle_fs_document_data(arg):
    values = {
        0: u'нет данных документа',
        1: u'получены данные документа'
    }

    return values[arg]


def handle_fs_shift_state(arg):
    values = {
        0: u'смена закрыта',
        1: u'смена открыта'
    }

    return values[arg]


def handle_fs_warning_flags(arg):
    values = (
        u'Превышено время ожидания ответа ОФД',
        u'Переполнение памяти ФН (Архив ФН заполнен на 90%)',
        u'Исчерпание ресурса криптографического сопроцессора (до окончания срока действия 30 дней)',
        u'Срочная замена криптографического сопроцессора (до окончания срока действия 3 дня)'
    )

    return dict(zip(values, misc.int_to_bits(arg, 4)))


def handle_info_exchange_state(arg):
    values = (
        u'Ожидание ответа на команду от ОФД',
        u'Изменились настройки соединения с ОФД',
        u'Есть команда от ОФД',
        u'Ожидание ответного сообщения (квитанции) от ОФД',
        u'Есть сообщение для передачи в ОФД',
        u'Транспортное соединение установлено'
    )

    return dict(zip(values, misc.int_to_bits(arg, 6)))
