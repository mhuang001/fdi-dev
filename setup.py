import os
from setuptools import setup

# https://pythonhosted.org/an_example_pypi_project/setuptools.html
#
# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="pns",
    version="0.1",
    author="Maohai Huang",
    author_email="mh@earth.bao.ac.cn",
    description=("Web API server for a data processing network node."),
    license="GPL",
    keywords="api processing dataset",
    url="http://mercury.bao.ac.cn:9006/mh/pns",
    packages=['pns'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPL License",
    ],
)
