# -*- coding: utf-8 -*-


from setuptools import setup

from pyshtrih import __version__


setup(
    name='pyshtrih',
    version=__version__,
    packages=['pyshtrih'],
    author='Oleg Golovanov',
    author_email='golovanov.ov@gmail.com',
    description='Реализация драйвера семейства ККМ "Штрих" на Python.',
    zip_safe=False,
    platforms='any',
    install_requires=['pyserial'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Office/Business :: Financial :: Point-Of-Sale',
        'Topic :: System :: Hardware :: Hardware Drivers'
        'Natural Language :: Russian',
    ]
)
