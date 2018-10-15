from setuptools import setup

PACKAGE_NAME = 'plumlightpad'

setup(
    name = PACKAGE_NAME,
    version = "0.0.11",
    author = "Heath Paddock",
    author_email = "hp@heathpaddock.com",
    description = ("A python package that interacts with the Plum Lightpad"),
    license = "MIT",
    keywords = ["plum", "lightpad"],
    url = "https://github.com/heathbar/plum-lightpad",
    packages = ['plumlightpad'],
    include_package_data = True,
    classifiers = [
        'Intended Audience :: Developers',
        "Development Status :: 4 - Beta",
        "Topic :: Home Automation",
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        "License :: OSI Approved :: MIT License",
    ],
)