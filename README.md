This software is used to package data into self-describing Data Products and make them portable in human-friendly format between data processers, storage, and consumers. The base data model is defined in package dataseet. Persistent data access, referencing, and Universal Resource Names are defined in package pal. A reference REST API server designed to communicate with a data processing docker using the data model is in package pns.

Product Access Layer allows data stored logical "pools" to be accessed with light weight product refernces by data processers, data storage, and data consumers. A data product can include a context built with references of relevant data. A ProductStorage interface is provided to handle saving/retrieving/querying data in registered pools.

Processing Network Server, a data processing pipeline/network node provides interfaces to make a run request to and read results from a processing task in a processing node via web APIs.

See [documents in HTML in doc/html/index.html](doc/html/index.html).

For more examples see tests/test_all.py
