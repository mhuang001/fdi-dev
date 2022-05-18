PYTEST	= python3 -m pytest
TESTLOG	= /tmp/fdi-tests.log
L	= INFO #WARNING
OPT	= -r P -v --no-cov-on-fail --no-cov -l --pdb -s --show-capture=all  --log-level=$(L)
T	= 
test: test1 test2 test5

testpns: test4

testhttp: test6 test7 test8 test9

test1: 
	$(PYTEST) tests/test_dataset.py -k 'not _mqtt' --cov=fdi/dataset $(OPT) $(T)

test2:
	$(PYTEST) tests/test_pal.py -k 'not _http and not _csdb' $(T) --cov=fdi/pal $(OPT)

test3:
	$(PYTEST)  $(OPT) -k 'server' $(T) tests/serv/test_pns.py --cov=fdi/pns

test4:
	$(PYTEST) $(OPT) -k 'not server' $(T) tests/serv/test_pns.py --cov=fdi/pns

test5:
	$(PYTEST)  $(OPT) $(T) tests/test_utils.py --cov=fdi/utils

test6:
	$(PYTEST) $(OPT) $(T) tests/serv/test_httppool.py

test7:
	$(PYTEST) $(OPT) $(T) tests/serv/test_httpclientpool.py -k 'not _csdb' $(T)

test8:
	$(PYTEST) $(OPT) tests/test_pal.py -k '_http and not _csdb' $(T)

test9:
	$(PYTEST) tests/test_dataset.py -k '_mqtt' $(T)

test10:
	$(PYTEST) $(OPT) tests/test_fits.py

test11:
	$(PYTEST) $(OPT) $(T) tests/serv/test_httpclientpool.py -k '_csdb' $(T)
	$(PYTEST) $(OPT) tests/test_pal.py -k '_csdb' $(T)

test12:
	$(PYTEST) $(OPT) tests/test_yaml2python.py
