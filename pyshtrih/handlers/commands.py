# -*- coding: utf-8 -*-


from . import functions as hf
from .. import misc


COMMANDS = {
    0x10: u'Короткий запрос состояния ФР',
    0x11: u'Запрос состояния ФР',
    0x13: u'Гудок',
    0x14: u'Установка параметров обмена',
    0x15: u'Чтение параметров обмена',
    0x16: u'Технологическое обнуление',
    0x17: u'Печать строки',
    0x19: u'Тестовый прогон',
    0x1A: u'Запрос денежного регистра',
    0x1B: u'Запрос операционного регистра',
    0x1E: u'Запись таблицы',
    0x1F: u'Чтение таблицы',
    0x21: u'Программирование времени',
    0x22: u'Программирование даты',
    0x23: u'Подтверждение программирования даты',
    0x25: u'Отрезка чека',
    0x28: u'Открыть денежный ящик',
    0x29: u'Протяжка',
    0x2B: u'Прерывание тестового прогона',
    0x2D: u'Запрос структуры таблицы',
    0x2E: u'Запрос структуры поля',
    0x40: u'Суточный отчет без гашения',
    0x41: u'Суточный отчет с гашением',
    0x50: u'Внесение',
    0x51: u'Выплата',
    0x80: u'Продажа',
    0x82: u'Возврат продажи',
    0x85: u'Закрытие чека',
    0x86: u'Скидка',
    0x87: u'Надбавка',
    0x88: u'Аннулирование чека',
    0x8C: u'Повтор документа',
    0x8D: u'Открыть чек',
    0xB0: u'Продолжение печати',
    0xC0: u'Загрузка графики',
    0xC1: u'Печать графики',
    0xC2: u'Печать штрих-кода',
    0xE0: u'Открыть смену',
    0xFC: u'Получить тип устройства',
    0xFF01: u'Запрос статуса ФН',
    0xFF03: u'Запрос срока действия ФН',
    0xFF08: u'Отменить документ в ФН',
    0xFF0A: u'Найти фискальный документ по номеру',
    0xFF0B: u'Открыть смену в ФН',
    0xFF0C: u'Передать произвольную TLV структуру',
    0xFF35: u'Начать формирование чека коррекции',
    0xFF36: u'Сформировать чек коррекции',
    0xFF38: u'Сформировать отчёт о состоянии расчётов',
    0xFF39: u'Получить статус информационного обмена',
    0xFF3F: u'Запрос количества ФД на которые нет квитанции',
    0xFF40: u'Запрос параметров текущей смены',
    0xFF41: u'Начать открытие смены',
    0xFF42: u'Начать закрытие смены',
    0xFF43: u'Закрыть смену в ФН'
}

ERROR_CODE_STR = u'Код ошибки'
ERROR_CODE_STRUCT = (slice(0, 1), misc.UNCAST_SIZE['1'], ERROR_CODE_STR)
OPERATOR_INDEX_NUMBER_STRUCT = (slice(1, 2), misc.UNCAST_SIZE['1'], u'Порядковый номер оператора')

HANDLERS = {
    # Короткий запрос состояния ФР
    0x10: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT,
        (slice(2, 4), misc.FuncChain(hf.handle_fr_flags, misc.UNCAST_SIZE['2']), u'Флаги ФР'),
        (slice(4, 5), misc.FuncChain(hf.FRMode, misc.UNCAST_SIZE['1']), u'Режим ФР'),
        (slice(5, 6), misc.FuncChain(hf.FRSubMode, misc.UNCAST_SIZE['1']), u'Подрежим ФР'),
        (misc.mslice(slice(11, 12), slice(6, 7)), misc.UNCAST_SIZE['2'], u'Количество операций в чеке'),
        (slice(7, 8), misc.UNCAST_SIZE['1'], u'Напряжение резервной батареи'),
        (slice(8, 9), misc.UNCAST_SIZE['1'], u'Напряжение источника питания'),
        (slice(9, 10), misc.UNCAST_SIZE['1'], u'Код ошибки ФП'),
        (slice(10, 11), misc.UNCAST_SIZE['1'], u'Код ошибки ЭКЛЗ'),
        (slice(12, 15), None, u'Зарезервировано')
    ),
    # Запрос состояния ФР
    0x11: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT,
        (slice(2, 4), misc.FuncChain(hf.handle_version, misc.UNCAST_SIZE['11']), u'Версия ПО ФР'),
        (slice(4, 6), misc.UNCAST_SIZE['2'], u'Сборка ПО ФР'),
        (slice(6, 9), misc.FuncChain(hf.handle_date, misc.UNCAST_SIZE['111']), u'Дата ПО ФР'),
        (slice(9, 10), misc.UNCAST_SIZE['1'], u'Номер в зале'),
        (slice(10, 12), misc.UNCAST_SIZE['2'], u'Сквозной номер текущего документа'),
        (slice(12, 14), misc.FuncChain(hf.handle_fr_flags, misc.UNCAST_SIZE['2']), u'Флаги ФР'),
        (slice(14, 15), misc.FuncChain(hf.FRMode, misc.UNCAST_SIZE['1']), u'Режим ФР'),
        (slice(15, 16), misc.FuncChain(hf.FRSubMode, misc.UNCAST_SIZE['1']), u'Подрежим ФР'),
        (slice(16, 17), misc.UNCAST_SIZE['1'], u'Порт ФР'),
        (slice(17, 19), misc.FuncChain(hf.handle_version, misc.UNCAST_SIZE['11']), u'Версия ПО ФП'),
        (slice(19, 21), misc.UNCAST_SIZE['2'], u'Сборка ПО ФП'),
        (slice(21, 24), misc.FuncChain(hf.handle_date, misc.UNCAST_SIZE['111']), u'Дата ПО ФП'),
        (slice(24, 27), misc.FuncChain(hf.handle_date, misc.UNCAST_SIZE['111']), u'Дата'),
        (slice(27, 30), misc.FuncChain(hf.handle_time, misc.UNCAST_SIZE['111']), u'Время'),
        (slice(30, 31), misc.FuncChain(hf.handle_fp_flags, misc.UNCAST_SIZE['1']), u'Флаги ФП'),
        (slice(31, 35), misc.UNCAST_SIZE['4'], u'Заводской номер'),
        (slice(35, 37), misc.UNCAST_SIZE['2'], u'Номер последней закрытой смены'),
        (slice(37, 39), misc.UNCAST_SIZE['2'], u'Количество свободных записей в ФП'),
        (slice(39, 40), misc.UNCAST_SIZE['1'], u'Количество перерегистраций (фискализаций)'),
        (slice(40, 41), misc.UNCAST_SIZE['1'], u'Количество оставшихся перерегистраций (фискализаций)'),
        (slice(41, 47), hf.handle_inn, u'ИНН')
    ),
    # Гудок
    0x13: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT,
    ),
    # Установка параметров обмена
    0x14: (
        ERROR_CODE_STRUCT,
    ),
    # Чтение параметров обмена
    0x15: (
        ERROR_CODE_STRUCT,
        (slice(1, 2), misc.FuncChain(hf.handle_baudrate, misc.UNCAST_SIZE['1']), u'Код скорости обмена'),
        (slice(2, 3), misc.FuncChain(hf.handle_byte_timeout, misc.UNCAST_SIZE['1']), u'Тайм аут приема байта')
    ),
    # Технологическое обнуление
    0x16: (
        ERROR_CODE_STRUCT,
    ),
    # Печать строки
    0x17: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Тестовый прогон
    0x19: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Запрос денежного регистра
    0x1A: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT,
        (slice(2, 8), misc.bytes_to_int, u'Содержимое регистра')
    ),
    # Запрос операционного регистра
    0x1B: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT,
        (slice(2, 4), misc.UNCAST_SIZE['2'], u'Содержимое регистра')
    ),
    # Запись таблицы
    0x1E: (
        ERROR_CODE_STRUCT,
    ),
    # Чтение таблицы
    0x1F: (
        ERROR_CODE_STRUCT,
        (slice(1, None), None, u'Значение'),
    ),
    # Программирование времени
    0x21: (
        ERROR_CODE_STRUCT,
    ),
    # Программирование даты
    0x22: (
        ERROR_CODE_STRUCT,
    ),
    # Подтверждение программирования даты
    0x23: (
        ERROR_CODE_STRUCT,
    ),
    # Отрезка чека
    0x25: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Открыть денежный ящик
    0x28: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Протяжка
    0x29: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Прерывание тестового прогона
    0x2B: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Запрос структуры таблицы
    0x2D: (
        ERROR_CODE_STRUCT,
        (slice(1, 41), misc.FuncChain(misc.decode, misc.bytearray_strip), u'Название таблицы'),
        (slice(41, 43), misc.UNCAST_SIZE['2'], u'Количество рядов'),
        (slice(43, 44), misc.UNCAST_SIZE['1'], u'Количество полей')
    ),
    # Запрос структуры поля
    0x2E: (
        ERROR_CODE_STRUCT,
        (slice(1, 41), misc.FuncChain(misc.decode, misc.bytearray_strip), u'Название поля'),
        (slice(41, 42), misc.FuncChain(hf.handle_type_field, misc.UNCAST_SIZE['1']), u'Тип поля'),
        (slice(42, None), hf.handle_min_max_field_value, None)
    ),
    # Суточный отчет без гашения
    0x40: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Суточный отчет с гашением
    0x41: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Внесение
    0x50: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT,
        (slice(2, None), misc.UNCAST_SIZE['2'], u'Сквозной номер документа')
    ),
    # Выплата
    0x51: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT,
        (slice(2, None), misc.UNCAST_SIZE['2'], u'Сквозной номер документа')
    ),
    # Продажа
    0x80: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Возврат продажи
    0x82: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Закрытие чека
    0x85: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT,
        (slice(2, 7), misc.bytes_to_int, u'Сдача')
    ),
    # Скидка
    0x86: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Надбавка
    0x87: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Аннулирование чека
    0x88: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Повтор документа
    0x8C: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Открыть чек
    0x8D: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Продолжение печати
    0xB0: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Загрузка графики
    0xC0: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Печать графики
    0xC1: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Печать штрих-кода
    0xC2: (
        ERROR_CODE_STRUCT,
        OPERATOR_INDEX_NUMBER_STRUCT
    ),
    # Открыть смену
    0xE0: (
        ERROR_CODE_STRUCT,
    ),
    # Получить тип устройства
    0xFC: (
        ERROR_CODE_STRUCT,
        (slice(1, 2), misc.UNCAST_SIZE['1'], u'Тип устройства'),
        (slice(2, 3), misc.UNCAST_SIZE['1'], u'Подтип устройства'),
        (slice(3, 4), misc.UNCAST_SIZE['1'], u'Версия протокола для данного устройства'),
        (slice(4, 5), misc.UNCAST_SIZE['1'], u'Подверсия протокола для данного устройства'),
        (slice(5, 6), misc.UNCAST_SIZE['1'], u'Модель устройства'),
        (slice(6, 7), misc.UNCAST_SIZE['1'], u'Язык устройства'),
        (slice(7, None), misc.decode, u'Название устройства')
    ),
    # Запрос статуса ФН
    0xFF01: (
        ERROR_CODE_STRUCT,
        (slice(1, 2), misc.FuncChain(hf.handle_fs_lifestate, misc.UNCAST_SIZE['1']), u'Состояние фазы жизни'),
        (slice(2, 3), misc.FuncChain(hf.handle_fs_current_document, misc.UNCAST_SIZE['1']), u'Текущий документ'),
        (slice(3, 4), misc.FuncChain(hf.handle_fs_document_data, misc.UNCAST_SIZE['1']), u'Данные документа'),
        (slice(4, 5), misc.FuncChain(hf.handle_fs_shift_state, misc.UNCAST_SIZE['1']), u'Состояние смены'),
        (slice(5, 6), misc.FuncChain(hf.handle_fs_warning_flags, misc.UNCAST_SIZE['1']), u'Флаги предупреждения'),
        (slice(6, 11), misc.FuncChain(hf.handle_datetime, misc.UNCAST_SIZE['11111']), u'Дата и время'),
        (slice(11, 27), None, u'Номер ФН'),
        (slice(27, 31), misc.UNCAST_SIZE['4'], u'Номер последнего ФД'),
    ),
    # Запрос срока действия ФН
    0xFF03: (
        ERROR_CODE_STRUCT,
        (slice(1, 4), misc.FuncChain(hf.handle_revdate, misc.UNCAST_SIZE['111']), u'Срок действия'),
        (slice(4, 5), misc.UNCAST_SIZE['1'], u'Кол-во оставшихся отчетов о перерегистрации'),
        (slice(5, 6), misc.UNCAST_SIZE['1'], u'Выполнено отчетов о перерегистрации')
    ),
    # Отменить документ в ФН
    0xFF08: (
        ERROR_CODE_STRUCT,
    ),
    # Найти фискальный документ по номеру
    0xFF0A: (
        ERROR_CODE_STRUCT,
        (slice(1, 2), misc.UNCAST_SIZE['1'], u'Тип фискального документа'),
        (slice(2, 3), misc.UNCAST_SIZE['1'], u'Получена ли квитанция из ОФД'),
        # TODO: реализовать разбор данных документа в зависимости от типа документа
        (slice(3, None), None, u'Данные фискального документа')
    ),
    # Открыть смену в ФН
    0xFF0B: (
        ERROR_CODE_STRUCT,
        (slice(1, 3), misc.UNCAST_SIZE['2'], u'Номер новой открытой смены'),
        (slice(3, 7), misc.UNCAST_SIZE['4'], u'Номер ФД'),
        (slice(7, 11), misc.UNCAST_SIZE['4'], u'Фискальный признак')
    ),
    # Передать произвольную TLV структуру
    0xFF0C: (
        ERROR_CODE_STRUCT,
    ),
    # Начать формирование чека коррекции
    0xFF35: (
        ERROR_CODE_STRUCT,
    ),
    # Сформировать чек коррекции
    0xFF36: (
        ERROR_CODE_STRUCT,
        (slice(1, 3), misc.UNCAST_SIZE['2'], u'Номер чека'),
        (slice(3, 7), misc.UNCAST_SIZE['4'], u'Номер ФД'),
        (slice(7, 11), misc.UNCAST_SIZE['4'], u'Фискальный признак')
    ),
    # Сформировать отчёт о состоянии расчётов
    0xFF38: (
        ERROR_CODE_STRUCT,
        (slice(1, 5), misc.UNCAST_SIZE['4'], u'Номер ФД'),
        (slice(5, 9), misc.UNCAST_SIZE['4'], u'Фискальный признак'),
        (slice(9, 13), misc.UNCAST_SIZE['4'], u'Количество неподтверждённых документов'),
        (
            slice(13, 16),
            misc.FuncChain(hf.handle_revdate, misc.UNCAST_SIZE['111']),
            u'Дата первого неподтверждённого документа'
        )
    ),
    # Получить статус информационного обмена
    0xFF39: (
        ERROR_CODE_STRUCT,
        (
            slice(1, 2),
            misc.FuncChain(hf.handle_info_exchange_state, misc.UNCAST_SIZE['1']),
            u'Статус информационного обмена'
        ),
        (slice(2, 3), misc.UNCAST_SIZE['1'], u'Состояние чтения сообщения'),
        (slice(3, 5), misc.UNCAST_SIZE['2'], u'Количество сообщений для ОФД'),
        (slice(5, 9), misc.UNCAST_SIZE['4'], u'Номер документа для ОФД первого в очереди'),
        (
            slice(9, 14),
            misc.FuncChain(hf.handle_datetime, misc.UNCAST_SIZE['11111']),
            u'Дата и время документа для ОФД первого в очереди'
        )
    ),
    # Запрос количества ФД на которые нет квитанции
    0xFF3F: (
        ERROR_CODE_STRUCT,
        (slice(1, 3), misc.UNCAST_SIZE['2'], u'Количество неподтверждённых ФД')
    ),
    # Запрос параметров текущей смены
    0xFF40: (
        ERROR_CODE_STRUCT,
        (slice(1, 2), misc.FuncChain(hf.handle_fs_shift_state, misc.UNCAST_SIZE['1']), u'Состояние смены'),
        (slice(2, 4), misc.UNCAST_SIZE['2'], u'Номер смены'),
        (slice(4, 6), misc.UNCAST_SIZE['2'], u'Номер чека')
    ),
    # Начать открытие смены
    0xFF41: (
        ERROR_CODE_STRUCT,
    ),
    # Начать закрытие смены
    0xFF42: (
        ERROR_CODE_STRUCT,
    ),
    # Закрыть смену в ФН
    0xFF43: (
        ERROR_CODE_STRUCT,
        (slice(1, 3), misc.UNCAST_SIZE['2'], u'Номер только что закрытой смены'),
        (slice(3, 7), misc.UNCAST_SIZE['4'], u'Номер ФД'),
        (slice(7, 11), misc.UNCAST_SIZE['4'], u'Фискальный признак')
    )
}
