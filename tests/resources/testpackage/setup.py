from setuptools import setup, find_packages, find_namespace_packages

setup(
    name='testpackage',
    version='0.1.1',
    # ,include=['testpackage']),
    packages=find_namespace_packages(where='.'),
    install_requires=[
    ],
    extras_require={
    },
    package_dir={"testpackage": "testpackage"},
    include_package_data=True,
    package_data={'': ['*.txt', '*.jsn', '*.json', '*.csv']},
    exclude_package_data={"": [".giti"]},
)
