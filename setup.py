import os
import re
from setuptools import setup

REQUIRES = []

PACKAGE_NAME = 'plumlightpad'

setup(
    name = PACKAGE_NAME,
    version = "0.0.7",
    author = "Heath Paddock",
    author_email = "hp@heathpaddock.com",
    description = ("A python package that interacts with the Plum Lightpad"),
    license = "MIT",
    keywords = ["plum", "lightpad"],
    url = "https://github.com/heathbar/plum-lightpad",
    packages=['plumlightpad'],
    include_package_data=True,
    install_requires=REQUIRES,
    classifiers=[
        'Intended Audience :: Developers',
        "Development Status :: 3 - Alpha",
        "Topic :: Home Automation",
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        "License :: OSI Approved :: MIT License",
    ],
)