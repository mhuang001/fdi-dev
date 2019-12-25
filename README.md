This software is used to package data into modular self-describing data products and make them portable in human-friendly format among data processors, stores, and consumers.

The base data model is defined in package ```dataset```. Persistent data access, referencing, and Universal Resource Names are defined in package ```pal```. A reference REST API server designed to communicate with a data processing server/docker using the data model is in package ```pns```.

To install
```
		cd /tmp
		git clone ssh://git@mercury.bao.ac.cn:9005/mh/spdc.git
		cd spdc
		pip3 install -e .
		
		mkdir ~/svom
		cd ~/svom
		cp /tmp/spdc/install .
		nano install [do some editing if needed]
		. ./install
```
change the git line to
```
		git clone http://mercury.bao.ac.cn:9006/mh/spdc.git
```
to install as a user.

Install the dependencies if needed ((python 3.6, Flask, pytest ...)
```
		cd /tmp/spdc
		pip3 install -r requirements.txt
```

See [documents in HTML in doc/html/index.html](doc/html/index.html).

For more examples see tests/test_*.py
