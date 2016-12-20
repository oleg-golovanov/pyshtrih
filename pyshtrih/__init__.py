# -*- coding: utf-8 -*-


from .utils import discovery
from .protocol import Protocol
from .device import ShtrihFRK, ShtrihFRPTK, ShtrihComboFRK, ShtrihComboPTK, ShtrihAllCommands
from .excepts import ProtocolError, NoConnectionError, UnexpectedResponseError, Error, CheckError, \
    OpenCheckError, ItemSaleError, CloseCheckError


__version__ = '1.6.1'
__all__ = (
    'discovery',
    'Protocol',
    'ShtrihFRK', 'ShtrihFRPTK', 'ShtrihComboFRK', 'ShtrihComboPTK', 'ShtrihAllCommands',
    'ProtocolError', 'NoConnectionError', 'UnexpectedResponseError', 'Error', 'CheckError',
    'OpenCheckError', 'ItemSaleError', 'CloseCheckError'
)
