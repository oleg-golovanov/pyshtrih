# -*- coding: utf-8 -*-


import sys


PY3 = sys.version_info.major >= 3


if PY3:
    import functools

    unicode = str
    xrange = range
    reduce = functools.reduce
else:
    unicode = unicode
    xrange = xrange
    reduce = reduce


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
