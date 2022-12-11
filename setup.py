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

pkgd = os.path.dirname(__file__)


def read(fname):
    return open(os.path.join(pkgd, fname), encoding='utf-8').read()


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
        'ruamel.yaml<0.17',
        'tabulate-expwidth>=0.9.0.1',
        # for actual use
        #'tabulate @ file://%s/resources/tabulate-0.8.10-py3-none-any.whl' % pkgd,
        # not uploadable for pypi
        #'tabulate @ git+https://github.com/mhuang001/python-tabulate.git@r1',
        #'tabulate @ git+http://mercury.bao.ac.cn:9006/mirrors/tabulate.git@r1',
        #'tabulate @ git+ssh://git@mercury.bao.ac.cn:9005/mirrors/tabulate.git@r1',
        'cwcwidth>=0.1.5',
        'paho-mqtt>=1.6.1',
        'jsonschema>=3.2.0',
        'xmltodict>=0.12.0',
        'jsonpath-ng>=1.5.3',
        'pypng',
        'networkx>=2.8.1',
        'pydot>=1.4.2'
    ],
    entry_points={'console_scripts': [
        'yaml2python=fdi.dataset.yaml2python:main',
        'fdi-getconfig=fdi.utils.getconfig:main',
    ]},
    setup_requires=[],
    tests_require=['pytest', 'pytest-cov', ],
    extras_require={
        'DEV': [
            'setuptools>=43.0.0',
            'wheel>=0.32.1',
            'pytest>=5.4.1',
            'pytest-cov',
            'remote-pdb',
            'asyncio',
            'aiohttp'
        ],
        'SERV': [
            'requests == 2.27.1',
            'urllib3 == 1.26.13',
            'Flask_HTTPAuth >= 4.1.0',
            'Flask>=2.2.2',
            'Werkzeug[watchdog]',
            'uwsgi>=2.0.20',
            'flasgger>=0.9.5',
        ],
        'SCI': [
            'astropy'
        ],
        'PUB': [
            'sphinx>=4.4.0',
            'sphinx_rtd_theme',
            'alabaster>=0.7.12',
            'sphinx-copybutton>=0.3.0',
            'twine>=3.3.0'
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Framework :: Flask",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    ],
)
