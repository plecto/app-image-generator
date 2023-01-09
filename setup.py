# encoding: utf-8
from setuptools import setup, find_packages
from app_image_generator import version

setup(
    name = 'app-image-generator',
    version = version,
    description = '',
    author = u'Kristian Øllegaard',
    author_email = 'kristian@oellegaard.com',
    zip_safe=False,
    include_package_data = True,
    packages = find_packages(exclude=[]),
    install_requires=['requests'],
    entry_points={
        'console_scripts': [
            'app-image-generator = app_image_generator.cli:main',
        ]
    },
)
