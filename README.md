This software helps data producers and processors to assemble and integrate data into modular datasets, offering human-friendly scripting APIs, exchange format among, and reference stores.

The base data model is defined in package ```dataset```. Persistent data access, referencing, and Universal Resource Names are defined in package ```pal```. A reference REST API server designed to communicate with a data processing server/docker using the data model is in package ```pns```.

To install
```
		cd /tmp
		git clone ssh://git@mercury.bao.ac.cn:9005/mh/fdi.git
		cd fdi
		pip3 install -e .
```
change the git line to
```
		git clone http://mercury.bao.ac.cn:9006/mh/fdi.git
```
to install as a user.

Install the dependencies if needed. python 3.6 for pal and pns, 2.7 for dataset

For more examples see tests/test_*.py

See [introduction, quick start, and API documents on readthedocs.io](https://fdi.readthedocs.io/en/latest/).

