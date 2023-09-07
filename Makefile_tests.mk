PYTEST	= python3 -m pytest
TESTLOG	= /tmp/fdi-tests.log
L	=
# --server can be 'mock' (default, ,background' (spawned) and 'external' real one given by config file.
OPT	=    --log-level=$(L) --server 'background'
OPT1	=    --log-level=$(L) --server 'external' -v
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
	$(PYTEST) tests/test_pal.py -k 'not _http and not _csdb' $(T)  $(OPT)

# --cov=fdi/pns
test3:
	$(PYTEST)  $(OPT) -k 'server' $(T) tests/serv/test_pns.py

#  --cov=fdi/pns
test4:
	$(PYTEST) $(OPT) -k 'not server' $(T) tests/serv/test_pns.py
# --cov=fdi/utils
test5:
	$(PYTEST)  $(OPT) $(T) tests/test_utils.py

test6:
	$(PYTEST) $(OPT) $(T) tests/serv/test_httppool.py 

test7:
	$(PYTEST) tests/test_server_setup.py $(OPT) $(T) -k '_pool_'

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
	$(PYTEST) $(OPT) tests/serv/test_thread.py $(T)
