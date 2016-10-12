# -*- coding: utf-8 -*-


from misc import LOCALE


class ProtocolError(IOError):
    pass


class NoConnectionError(ProtocolError):
    pass


class UnexpectedResponseError(ProtocolError):
    pass


class Error(ProtocolError):

    codes = {
        0x00: u'Ошибок нет',
        0x01: u'Неисправен накопитель ФП 1, ФП 2 или часы',
        0x02: u'Отсутствует ФП 1',
        0x03: u'Отсутствует ФП 2',
        0x04: u'Некорректные параметры в команде обращения к ФП',
        0x05: u'Нет запрошенных данных',
        0x06: u'ФП в режиме вывода данных',
        0x07: u'Некорректные параметры в команде для данной реализации ФП',
        0x08: u'Команда не поддерживается в данной реализации ФП',
        0x09: u'Некорректная длина команды',
        0x0A: u'Формат данных не BCD',
        0x0B: u'Неисправна ячейка памяти ФП при записи итога',
        0x11: u'Не введена лицензия',
        0x12: u'Заводской номер уже введен',
        0x13: u'Текущая дата меньше даты последней записи в ФП',
        0x14: u'Область сменных итогов ФП переполнена',
        0x15: u'Смена уже открыта',
        0x16: u'Смена не открыта',
        0x17: u'Номер первой смены больше номера последней смены',
        0x18: u'Дата первой смены больше даты последней смены',
        0x19: u'Нет данных в ФП',
        0x1A: u'Область перерегистраций в ФП переполнена',
        0x1B: u'Заводской номер не введен',
        0x1C: u'В заданном диапазоне есть поврежденная запись',
        0x1D: u'Повреждена последняя запись сменных итогов',
        0x1E: u'Область перерегистраций ФП переполнена',
        0x1F: u'Отсутствует память регистров',
        0x20: u'Переполнение денежного регистра при добавлении',
        0x21: u'Вычитаемая сумма больше содержимого денежного регистра',
        0x22: u'Неверная дата',
        0x23: u'Нет записи активизации',
        0x24: u'Область активизаций переполнена',
        0x25: u'Нет активизации с запрашиваемым номером',
        0x26: u'Вносимая клиентом сумма меньше суммы чека',
        0x2B: u'Невозможно отменить предыдущую команду',
        0x2C: u'Обнулённая касса (повторное гашение невозможно)',
        0x2D: u'Сумма чека по секции меньше суммы сторно',
        0x2E: u'В ФР нет денег для выплаты',
        0x30: u'ФР заблокирован, ждет ввода пароля налогового инспектора',
        0x32: u'Требуется выполнение общего гашения',
        0x33: u'Некорректные параметры в команде',
        0x34: u'Нет данных',
        0x35: u'Некорректный параметр при данных настройках',
        0x36: u'Некорректные параметры в команде для данной реализации ФР',
        0x37: u'Команда не поддерживается в данной реализации ФР',
        0x38: u'Ошибка в ПЗУ',
        0x39: u'Внутренняя ошибка ПО ФР',
        0x3A: u'Переполнение накопления по надбавкам в смене',
        0x3B: u'Переполнение накопления в смене',
        0x3C: u'Смена открыта – ФР: операция невозможна или ЭКЛЗ: неверный регистрационный номер',
        0x3D: u'Смена не открыта – операция невозможна',
        0x3E: u'Переполнение накопления по секциям в смене',
        0x2F: u'Переполнение накопления по скидкам в смене',
        0x40: u'Переполнение диапазона скидок',
        0x41: u'Переполнение диапазона оплаты наличными',
        0x42: u'Переполнение диапазона оплаты типом 2',
        0x43: u'Переполнение диапазона оплаты типом 3',
        0x44: u'Переполнение диапазона оплаты типом 4',
        0x45: u'Сумма всех типов оплаты меньше итога чека',
        0x46: u'Не хватает наличности в кассе',
        0x47: u'Переполнение накопления по налогам в смене',
        0x48: u'Переполнение итога чека',
        0x49: u'Операция невозможна в открытом чеке данного типа',
        0x4A: u'Открыт чек – операция невозможна',
        0x4B: u'Буфер чека переполнен',
        0x4C: u'Переполнение накопления по обороту налогов в смене',
        0x4D: u'Вносимая безналичной оплатой сумма больше суммы чека',
        0x4E: u'Смена превысила 24 часа',
        0x4F: u'Неверный пароль',
        0x50: u'Идет печать предыдущей команды',
        0x51: u'Переполнение накоплений наличными в смене',
        0x52: u'Переполнение накоплений по типу оплаты 2 в смене',
        0x53: u'Переполнение накоплений по типу оплаты 3 в смене',
        0x54: u'Переполнение накоплений по типу оплаты 4 в смене',
        0x55: u'Чек закрыт – операция невозможна',
        0x56: u'Нет документа для повтора',
        0x57: u'ЭКЛЗ: количество закрытых смен не совпадает с ФП',
        0x58: u'Ожидание команды продолжения печати',
        0x59: u'Документ открыт другим оператором',
        0x5A: u'Скидка превышает накопления в чеке',
        0x5B: u'Переполнение диапазона надбавок',
        0x5C: u'Понижено напряжение 24В',
        0x5D: u'Таблица не определена',
        0x5E: u'Некорректная операция',
        0x5F: u'Отрицательный итог чека',
        0x60: u'Переполнение при умножении',
        0x61: u'Переполнение диапазона цены',
        0x62: u'Переполнение диапазона количества',
        0x63: u'Переполнение диапазона отдела',
        0x64: u'ФП отсутствует',
        0x65: u'Не хватает денег в секции',
        0x66: u'Переполнение денег в секции',
        0x67: u'Ошибка связи с ФП',
        0x68: u'Не хватает денег по обороту налогов',
        0x69: u'Переполнение денег по обороту налогов',
        0x6A: u'Ошибка питания в момент ответа по I2C',
        0x6B: u'Нет чековой ленты',
        0x6C: u'Нет контрольной ленты',
        0x6D: u'Не хватает денег по налогу',
        0x6E: u'Переполнение денег по налогу',
        0x6F: u'Переполнение по выплате в смене',
        0x70: u'Переполнение ФП',
        0x71: u'Ошибка отрезчика',
        0x72: u'Команда не поддерживается в данном подрежиме',
        0x73: u'Команда не поддерживается в данном режиме',
        0x74: u'Ошибка ОЗУ',
        0x75: u'Ошибка питания',
        0x76: u'Ошибка принтера: нет импульсов с тахогенератора',
        0x77: u'Ошибка принтера: нет сигнала с датчиков',
        0x78: u'Замена ПО',
        0x79: u'Замена ФП',
        0x7A: u'Поле не редактируется',
        0x7B: u'Ошибка оборудования',
        0x7C: u'Не совпадает дата',
        0x7D: u'Неверный формат даты',
        0x7E: u'Неверное значение в поле длины',
        0x7F: u'Переполнение диапазона итога чека',
        0x80: u'Ошибка связи с ФП',
        0x81: u'Ошибка связи с ФП',
        0x82: u'Ошибка связи с ФП',
        0x83: u'Ошибка связи с ФП',
        0x84: u'Переполнение наличности',
        0x85: u'Переполнение по продажам в смене',
        0x86: u'Переполнение по покупкам в смене',
        0x87: u'Переполнение по возвратам продаж в смене',
        0x88: u'Переполнение по возвратам покупок в смене',
        0x89: u'Переполнение по внесению в смене',
        0x8A: u'Переполнение по надбавкам в чеке',
        0x8B: u'Переполнение по скидкам в чеке',
        0x8C: u'Отрицательный итог надбавки в чеке',
        0x8D: u'Отрицательный итог скидки в чеке',
        0x8E: u'Нулевой итог чека',
        0x8F: u'Касса не фискализирована',
        0x90: u'Поле превышает размер, установленный в настройках',
        0x91: u'Выход за границу поля печати при данных настройках шрифта',
        0x92: u'Наложение полей',
        0x93: u'Восстановление ОЗУ прошло успешно',
        0x94: u'Исчерпан лимит операций в чеке',
        0xA0: u'Ошибка связи с ЭКЛЗ',
        0xA1: u'ЭКЛЗ отсутствует',
        0xA2: u'ЭКЛЗ: Некорректный формат или параметр команды',
        0xA3: u'Некорректное состояние ЭКЛЗ',
        0xA4: u'Авария ЭКЛЗ',
        0xA5: u'Авария КС в составе ЭКЛЗ',
        0xA6: u'Исчерпан временной ресурс ЭКЛЗ',
        0xA7: u'ЭКЛЗ переполнена',
        0xA8: u'ЭКЛЗ: Неверные дата и время',
        0xA9: u'ЭКЛЗ: Нет запрошенных данных',
        0xAA: u'Переполнение ЭКЛЗ (отрицательный итог документа)',
        0xB0: u'ЭКЛЗ: Переполнение в параметре количество',
        0xB1: u'ЭКЛЗ: Переполнение в параметре сумма',
        0xB2: u'ЭКЛЗ: Уже активизирована',
        0xC0: u'Контроль даты и времени (подтвердите дату и время)',
        0xC1: u'ЭКЛЗ: суточный отчёт с гашением прервать нельзя',
        0xC2: u'Превышение напряжения в блоке питания',
        0xC3: u'Несовпадение итогов чека и ЭКЛЗ',
        0xC4: u'Несовпадение номеров смен',
        0xC5: u'Буфер подкладного документа пуст',
        0xC6: u'Подкладной документ отсутствует',
        0xC7: u'Поле не редактируется в данном режиме',
        0xC8: u'Отсутствуют импульсы от таходатчика'
    }

    def __init__(self, code):
        self.code = code
        self.msg = self.codes.get(code, u'Неизвестная ошибка')

    def __str__(self):
        return self.msg.encode(LOCALE)

    def __unicode__(self):
        return self.msg

    def __repr__(self):
        return '{}({}, {})'.format(type(self).__name__, self.code, self)


class CheckError(Error):

    def __init__(self, exc):
        if not isinstance(exc, Error):
            raise ValueError(
                u'Ожидался экземпляр {}, получен {}'.format(Error.__name__, type(exc).__name__)
            )
        super(CheckError, self).__init__(exc.code)


OpenCheckError = CheckError
ItemSaleError = CheckError
CloseCheckError = CheckError
