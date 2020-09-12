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

If plan to compile doc, install the dependencies:
```
		make install_with_DOC
```

To uninstall:
```
		make uninstall
```

To generate ```baseproduct.py``` and ```product.py``` from schema in fdi/dataset/resources```:
```
		make py
```

For more examples see tests/test_*.py

See [introduction, quick start, and API documents on readthedocs.io](https://fdi.readthedocs.io/en/latest/).

