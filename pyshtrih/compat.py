# -*- coding: utf-8 -*-


import sys
import locale


PY2 = sys.version_info.major == 2
LOCALE = locale.getpreferredencoding()


if PY2:
    unicode = unicode
    xrange = xrange
    reduce = reduce
else:
    import functools

    unicode = str
    xrange = range
    reduce = functools.reduce


# Взято из six
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instantiation that replaces
    # itself with the actual metaclass.
    class metaclass(type):
        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)

    return type.__new__(metaclass, 'temporary_class', (), {})


def str_compat(cls):
    if PY2:
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda self: self.__unicode__().encode(LOCALE)
        # перепривязываем __repr__
        if hasattr(cls, '__repr__') and cls.__repr__ == cls.__unicode__:
            cls.__repr__ = cls.__str__

    return cls


def bool_compat(cls):
    if PY2:
        cls.__nonzero__ = cls.__bool__

    return cls
