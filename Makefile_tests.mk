PYEXE	= python3
PYTEST = env -u PNS_CLOUD_USER -u PNS_CLOUD_PASS -u PNS_CLOUD_TOKEN $(PYEXE) -m pytest
PYTEST = pytest
TESTLOG	= /tmp/fdi-tests.log
L	=
SV	= background
# --server can be 'mock' (default, ,background' (spawned) and 'external' real one given by config file.
OPT	= -v  --log-level=$(L) --server=$(SV) -r P --id=44
OPT1	= -v --log-level=$(L) --server=external
T	= 
test: test1 test2 test5 test13 test14 test10

testhttp: test7 test8 test9 #test15
	@echo SERVRE OPTION: $(OPT)

testcsdb: test11 test16 
	@echo SERVRE OPTION: $(OPT)

testpns: test4


test1: 
	$(PYTEST) tests/test_dataset.py  -k 'not _mqtt' $(OPT) $(T)

# --cov=fdi/pal
test2:
	$(PYTEST) tests/test_pal.py -k 'not _http and not _csdb'  $(OPT) $(T) 

# --cov=fdi/pns
test3:
	$(PYTEST)  $(OPT) -k 'server' $(T) tests/serv/test_pns.py

#  --cov=fdi/pns
test4:
	$(PYTEST) $(OPT) -k 'not server' $(T) tests/serv/test_pns.py
# --cov=fdi/utils
test5:
	$(PYTEST)  $(OPT) tests/test_utils.py $(T) 

test6:
	$(PYTEST) $(OPT) tests/serv/test_httppool.py  $(T) 

test7:
	$(PYTEST) tests/test_server_setup.py $(OPT) $(T) -k '_pool_' --log-level=DEBUG

	$(PYTEST) $(OPT) tests/serv/test_httpclientpool.py -k 'not _csdb' $(T)

test8:
	$(PYTEST) $(OPT) tests/test_pal.py -k '_http and not _csdb' $(T)

test9:
	$(PYTEST) $(OPT) tests/test_dataset.py -k '_mqtt' $(T)

test10:
	$(PYTEST) $(OPT) tests/test_fits.py $(T)

test11:
	$(PYTEST) tests/test_server_setup.py $(OPT1) $(T) -k 'csdb'
	$(PYTEST) $(OPT1) tests/serv/test_csdb.py $(T)

test16:
	$(PYTEST) $(OPT1) tests/test_pal.py -k _csdb $(T)

test12:
	$(PYTEST) $(OPT) tests/test_yaml2python.py $(T)

test13:
	$(PYTEST) $(OPT) tests/test_schemas.py $(T)


test14:
	$(PYTEST) $(OPT) tests/test_classes.py $(T)

test15:
	$(PYTEST) $(OPT) --id test_threaded tests/serv/test_thread.py $(T)

U = http://127.0.0.1:9885/fdi/v0.16
P = 
test16:
	# clear up remain login info
	curl -i -X GET $(U)/logout
	curl -i -X GET $(U)/logout
	rsp = `curl -i -X GET $(U)/`
	print(rsp)
	curl -i -X GET $(U)/logout
	print(rsp)
