# -*- coding: utf-8 -*-


import misc


class FD(object):
    TAGS = {
        # тэг: (тип значения, признак обязательности соблюдения длины, максимальная длина)
        # телефон или электронный адрес покупателя
        1008: (unicode, False, 64),
        # адрес расчетов
        1009: (unicode, False, 256),
        # кассир
        1021: (unicode, False, 64),
        # место расчетов
        1087: (unicode, False, 256),
        # наименование поставщика
        1225: (unicode, False, 256)
    }

    CAST = {
        unicode: lambda x: x.encode('cp866')
    }
    LEN = {
        str: len
    }

    def __init__(self, **kwargs):
        self.data = bytearray()
        for item in kwargs.items():
            self.set_value(*item)

    def set_value(self, tag, value):
        try:
            type_, len_req, len_max = self.TAGS.get(tag)
        except TypeError:
            raise ValueError(u'Тэг {} не поддерживается'.format(tag))

        value_type = type(value)
        if value_type != type_:
            raise ValueError(
                u'Значение для тэга {} должно быть {}, получено {}'.format(tag, type_, value_type)
            )

        cast_call = self.CAST.get(type(value))
        if cast_call:
            value = cast_call(value)

        value = value[:len_max]

        self.data.extend(
            misc.bytearray_concat(
                misc.CAST_SIZE['2'](tag),
                misc.CAST_SIZE['2'](len(value)),
                value
            )
        )

    def dump(self):
        return bytes(self.data)
