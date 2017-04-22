# -*- coding: utf8 -*-

import codecs
from setuptools import setup


with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="zcache",
    version="0.0.1",
    license='http://www.apache.org/licenses/LICENSE-2.0',
    author='zhuyu',
    author_email='yolkking@126.com',
    package_data={
        'zcache': ['README.rst', 'LICENSE']
    },
    install_requires=[],
    entry_points="""
    [console_scripts]
    zcache = zcache.main:main
    """,
    long_description=long_description,
)