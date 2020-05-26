import os
from setuptools import setup, find_packages

# https://pythonhosted.org/an_example_pypi_project/setuptools.html
# https://code.tutsplus.com/tutorials/how-to-write-package-and-distribute-a-library-in-python--cms-28693
#


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="fdi",
    version="0.16",
    author="Maohai Huang",
    author_email="mhuang@earth.bao.ac.cn",
    description=("Flexible Data Integrator"),
    license="LGPL",
    keywords="dataset metadata processing context server access REST API HCSS",
    url="http://mercury.bao.ac.cn:9006/mh/fdi",
    packages=find_packages(exclude=['tests', 'tmp']),
    long_description=read('README.md'),
    python_requires=">=3.6",
    install_requires=[
        'setuptools',
        'pytest>=5.4.1',
        'nox>=2019.11.9',
        'requests>=2.23.0',
        'filelock>=3.0.12',
        'aiohttp_theme>=0.1.6',
        'aiohttp>=3.6.2',
        'sphinx_rtd_theme>=0.4.3',
        'Flask_HTTPAuth>=3.3.0',
        'Flask>=1.1.2',
        'PyYAML>=5.3.1',
        'sphinx-copybutton @ git+http://github.com/mhuang001/sphinx-copybutton.git#egg=sphinx-copybutton-0.2.12.dev0'
    ],
    classifiers=[
        "Development Status :: 3 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPL License",
    ],
)
