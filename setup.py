import os
from setuptools import setup

#
#
# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="dataset",
    version="0.1",
    author="Maohai Huang",
    author_email="mhuang@earth.bao.ac.cn",
    description=("packaging data into self-describing Data Products"),
    license="GPL",
    keywords="dataset product metadata HCSS",
    url="http://mercury.bao.ac.cn:9006/mh/dataset",
    packages=['dataset', 'tests'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPL License",
    ],
)
