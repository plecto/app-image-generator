# encoding: utf-8
from setuptools import setup, find_packages
from dynpacker import version

setup(
    name = 'dynpacker',
    version = version,
    description = '',
    author = u'Kristian Øllegaard',
    author_email = 'kristian@oellegaard.com',
    zip_safe=False,
    include_package_data = True,
    packages = find_packages(exclude=[]),
    install_requires=[],
)