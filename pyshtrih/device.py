# -*- coding: utf-8 -*-


from driver import Driver
from excepts import NoItemsError


SALE_CHECK = 0
RETURN_SALE_CHECK = 2


class Device(Driver):
    CONTROL_TAPE = False
    CASH_TAPE = False

    def print_rows(self, *rows):
        for row in rows:
            self.print_string(row, control_tape=self.CONTROL_TAPE, cash_tape=self.CASH_TAPE)

    def print_header(self, *items):
        """
        Печать заголовка чека.

        :param items: набор строк заголовка
        """

        self.print_rows(*items)
        self.print_line(control_tape=self.CONTROL_TAPE, cash_tape=self.CASH_TAPE)

    def print_footer(self, *items):
        """
        Печать подвала чека.

        :param items: набор строк подвала
        """

        if items:
            self.print_line(control_tape=self.CONTROL_TAPE, cash_tape=self.CASH_TAPE)
        self.print_rows(*items)

    def checkout_sale(self, cash, header, items, footer, allowance=0, discount=0):
        """
        Печать чека продажи.
        """

        self.print_header(*header)

        if items:
            self.open_check(SALE_CHECK)
            for item in items:
                self.sale(item)
            self.allowance(allowance)
            self.discount(discount)
            self.close_check(cash)

        self.print_footer(*footer)

    def checkout_return_sale(self, sum_, header, items, footer):
        """
        Печать чека возврата продажи.
        """

        if not items:
            raise NoItemsError(u'Отсутствуют позиции возврата продажи')

        self.print_header(*header)

        self.open_check(RETURN_SALE_CHECK)
        for item in items:
            self.return_sale(item)
        self.close_check(sum_)

        self.print_footer(*footer)


class ShtrihFRK(Device):
    CONTROL_TAPE = True
    CASH_TAPE = True
    DEFAULT_MAX_LENGTH = 36


class ShtrihComboFRK(Device):
    CASH_TAPE = True
    DEFAULT_MAX_LENGTH = 48


ShtrihComboPTK = ShtrihComboFRK
