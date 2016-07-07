# -*- coding: utf-8 -*-


from re import search
from os.path import join, dirname

from setuptools import setup


with open(join(dirname(__file__), 'pyshtrih', '__init__.py')) as f:
    version = search(r'__version__\s+=\s+[\'\"]+(.*)[\'\"]+', f.read()).group(1)


setup(
    name='pyshtrih',
    version=version,
    packages=['pyshtrih'],
    url='https://github.com/oleg-golovanov/pyshtrih',
    license='MIT',
    author='Oleg Golovanov',
    author_email='golovanov.ov@gmail.com',
    description='Реализация драйвера семейства ККМ "Штрих" на Python.',
    zip_safe=False,
    platforms='any',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
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
        'Topic :: System :: Hardware :: Hardware Drivers',
        'Natural Language :: Russian',
    ]
)
