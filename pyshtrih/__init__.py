# -*- coding: utf-8 -*-


from .utils import discovery
from .protocol import Protocol
from .device import ShtrihFRK, ShtrihFRPTK, ShtrihComboFRK, ShtrihComboPTK, ShtrihLightPTK, ShtrihAllCommands
from .excepts import ProtocolError, NoConnectionError, UnexpectedResponseError, Error, CheckError, \
    OpenCheckError, ItemSaleError, CloseCheckError


__version__ = '1.6.4'
__all__ = (
    'discovery',
    'Protocol',
    'ShtrihFRK', 'ShtrihFRPTK', 'ShtrihComboFRK', 'ShtrihComboPTK', 'ShtrihLightPTK', 'ShtrihAllCommands',
    'ProtocolError', 'NoConnectionError', 'UnexpectedResponseError', 'Error', 'CheckError',
    'OpenCheckError', 'ItemSaleError', 'CloseCheckError'
)
