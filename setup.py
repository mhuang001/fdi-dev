import os
from setuptools import setup, find_packages

# https://pythonhosted.org/an_example_pypi_project/setuptools.html
# https://code.tutsplus.com/tutorials/how-to-write-package-and-distribute-a-library-in-python--cms-28693
#

# Version info -- read without importing
# https://github.com/aio-libs/aiohttp-theme/blob/master/setup.py
_locals = {}
with open('fdi/_version.py') as fp:
    exec(fp.read(), None, _locals)
version = _locals['__version__']


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="fdi",
    version=version,
    author="Maohai Huang",
    author_email="mhuang@earth.bao.ac.cn",
    description=("Flexible Data Integrator"),
    license="LGPL v3",
    keywords="dataset metadata processing product context serialization server URN RESTful API HCSS",
    url="http://mercury.bao.ac.cn:9006/mh/fdi",
    packages=find_packages(exclude=['tests', 'tmp', 'docs']),
    include_package_data=True,
    long_description=read('README.rst'),
    long_description_content_type="text/x-rst",
    python_requires=">=3.6",
    install_requires=[
        'requests>=2.23.0',
        'filelock>=3.0.12',
        'ruamel.yaml>=0.15.0',
        'tabulate>=0.8.7',
        'paho-mqtt>=1.5.1',
    ],
    entry_points={'console_scripts': [
        'yaml2python=fdi.dataset.yaml2python:main']},
    setup_requires=[],
    tests_require=['pytest', 'pytest-cov', ],
    extras_require={
        'DEV': [
            'setuptools>=43.0.0',
            'wheel>=0.32.1',
            'pytest>=5.4.1',
            'pytest-cov',
            'aiohttp>=3.6.2',
        ],
        'SERV': [
            'Flask_HTTPAuth>=3.3.0',
            'Flask>=1.1.2',
            'waitress>=2.0.0'
        ],
        'PUB': [
            'sphinx_rtd_theme>=0.4.3',
            'sphinx-copybuttono>=0.3.0',
            'twine>=3.3.0'
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Framework :: Flask",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    ],
)
