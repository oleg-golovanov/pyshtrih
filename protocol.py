# -*- coding: utf-8 -*-


import serial

from misc import mslice, lrc, bytearray_cast, bytearray_concat, encode, CAST_SIZE, UNCAST_SIZE, LOCALE
from handlers import HANDLERS, ERROR_CODE_STR


STX = bytearray.fromhex('02')
ENQ = bytearray.fromhex('05')
ACK = bytearray.fromhex('06')  # положительное подтверждение
NAK = bytearray.fromhex('15')  # отрицательное подтверждение


class ProtocolError(IOError):
    pass


class NoConnectionError(ProtocolError):
    pass


class UnexpectedResponseError(ProtocolError):
    pass


class Error(ProtocolError):
    codes = {
        0x0: u'Ошибок нет',
        0x1: u'Неисправен накопитель ФП 1, ФП 2 или часы',
        0x2: u'Отсутствует ФП 1',
        0x3: u'Отсутствует ФП 2',
        0x4: u'Некорректные параметры в команде обращения к ФП',
        0x5: u'Нет запрошенных данных',
        0x6: u'ФП в режиме вывода данных',
        0x7: u'Некорректные параметры в команде для данной реализации ФП',
        0x8: u'Команда не поддерживается в данной реализации ФП',
        0x9: u'Некорректная длина команды',
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
        0xC0: u'Контроль даты и времени (подтвердите дату и время)'
    }

    def __init__(self, code):
        self.code = code
        self.msg = self.codes.get(code, u'Неизвестная ошибка')

    def __str__(self):
        return self.msg.encode(LOCALE)

    def __unicode__(self):
        return self.msg

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.code, self)


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
                parity = serial.PARITY_NONE,
                stopbits = serial.STOPBITS_ONE,
                timeout = self.timeout,
                writeTimeout = self.timeout
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

    def command_nopass(self, cmd, params = bytearray()):
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

    DEFAULT_CASHIER_PASSWORD = 1
    DEFAULT_ADMIN_PASSWORD = 30

    DEFAULT_MAX_LENGTH = 48

    TABLES_COUNT = 15

    # TODO: подумать можно ли избавиться от port и baudrate в пользу автоматического поиска устройства
    def __init__(self, port = '/dev/ttyS0', baudrate = 9600, timeout = None, password = None, admin_password = None):
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

        return self.protocol.command(
            0x17, self.password, CAST_SIZE['1'](control + cash), encode(string[:self.DEFAULT_MAX_LENGTH])
        )

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

    def cut(self, partial = False):
        """
        Обрезка чека.
        """

        return self.protocol.command(0x25, self.password, CAST_SIZE['1'](partial))

    def open_drawer(self, box):
        """
        Открыть денежный ящик.
        """

        return self.protocol.command(0x28, self.password, CAST_SIZE['1'](box))

    def test_stop(self):
        """
        Прерывание тестового прогона.
        """

        return self.protocol.command(0x2B, self.password)

    def x_report(self):
        """
        Суточный отчет без гашения.
        """

        return self.protocol.command(0x40, self.admin_password)

    def z_report(self):
        """
        Суточный отчет с гашением.
        """

        return self.protocol.command(0x41, self.admin_password)

    def income (self, sum):
        """
        Внесение.
        """

        return self.protocol.command(0x50, self.password, CAST_SIZE['41'](round(sum * 100), 0))

    def outcome (self, sum):
        """
        Выплата.
        """

        return self.protocol.command(0x51, self.password, CAST_SIZE['41'](round(sum * 100), 0))

    def repeat (self):
        """
        Повтор документа.
        """

        return self.protocol.command(0x8C, self.password)

    def continue_print (self, password):
        """
        Продолжение печати.
        """

        return self.protocol.command(0xB0, password)

    def open_shift(self):
        """
        Открыть смену.
        """

        return self.protocol.command(0xE0, self.password)

    def model(self):
        return self.protocol.command_nopass(0xFC)

    # def checkout (self):
    #     '''
    #     Регистрация и печать чека
    #     '''
    #     raise NotImplementedError ('checkout() is not implemented')
    #
    # def shift_is_open (self):
    #     raise NotImplementedError ('shift_is_open() is not implemented')
    #
    # def cancel_check (self):
    #     raise NotImplementedError ('cancel_check() is not implemented')
    #
    # def storno (self):
    #     '''
    #     Сторнирование документа
    #     '''
    #     raise NotImplementedError ('storno() is not implemented')


if __name__ == '__main__':
    import time
    p = Driver()
    p.connect()
    # print(repr(p.command(0x13, p.DEFAULT_CASHIER_PASSWORD)).decode('unicode-escape'))
#    print(repr(p.test_start(1)).decode('unicode-escape'))
#    print(repr(p.income(50.236)).decode('unicode-escape'))
#    time.sleep (1)
    print(repr(p.repeat ()).decode('unicode-escape'))
    # print(repr(p.command_nopass(0xFC)).decode('unicode-escape'))
