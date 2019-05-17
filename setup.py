import os
from setuptools import setup, find_packages

# https://pythonhosted.org/an_example_pypi_project/setuptools.html
# https://code.tutsplus.com/tutorials/how-to-write-package-and-distribute-a-library-in-python--cms-28693
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
    description=("Self-describing Data Product Container"),
    license="GPL",
    keywords="dataset product metadata HCSS",
    url="http://mercury.bao.ac.cn:9006/mh/dataset",
    packages=find_packages(exclude=['tests']),
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPL License",
    ],
)
