"""Setup."""
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

setup(
    name='tap-adyen',
    version='0.2.1',
    description='Singer.io tap for extracting data from Adyen',
    author='Stitch',
    url='https://github.com/Yoast/singer-tap-adyen',
    classifiers=['Programming Language :: Python :: 3 :: Only'],
    py_modules=['tap_adyen'],
    install_requires=[
        'requests==2.28.1',
        'python-dateutil==2.8.2',
        'singer-python==5.12.2',
    ],
    entry_points="""
        [console_scripts]
        tap-adyen=tap_adyen:main
    """,
    packages=find_packages(),
    package_data={
        'tap_adyen': [
            'schemas/*.json',
        ],
    },
    include_package_data=True,
)
