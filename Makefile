PRODUCT = Product
B_PRODUCT = BaseProduct
PYDIR	= fdi/dataset
RESDIR	= $(PYDIR)/resources
P_PY	= $(shell python -S -c "print('$(PRODUCT)'.lower())").py
B_PY	= $(shell python -S -c "print('$(B_PRODUCT)'.lower())").py
B_INFO	= $(B_PY)
P_YAML	= $(RESDIR)
B_YAML	= $(RESDIR)
P_TEMPLATE	= $(RESDIR)
B_TEMPLATE	= $(RESDIR)

py: $(PYDIR)/$(B_PY) $(PYDIR)/$(P_PY)

$(PYDIR)/$(P_PY): $(PYDIR)/yaml2python.py $(P_YAML) $(P_TEMPLATE)/$(PRODUCT).template $(PYDIR)/$(B_PY)
	python3 -m fdi.dataset.yaml2python -y $(P_YAML) -t $(P_TEMPLATE) -o $(PYDIR) $(Y)


$(PYDIR)/$(B_PY): $(PYDIR)/yaml2python.py $(B_YAML) $(B_TEMPLATE)/$(B_PRODUCT).template 
	python3 -m fdi.dataset.yaml2python -y $(P_YAML) -t $(P_TEMPLATE) -o $(PYDIR) $(Y)

yamlupgrade: 
	python3 -m fdi.dataset.yaml2python -y $(P_YAML) -u


.PHONY: runserver runpoolserver reqs install uninstall vtag FORCE \
	test test1 test2 test3 test4 test5\
	plots plotall plot_dataset plot_pal plot_pns \
	docs docs_api docs_plots docs_html

# extra option for 'make runserver S=...'
S	=
# default username and password are in pnsconfig.py
runserver:
	python3 -m fdi.pns.runflaskserver --username=foo --password=bar -v $(S)
runpoolserver:
	python3 -m fdi.pns.runflaskserver --username=foo --password=bar --server=httppool_server -v $(S)

INSOPT  =
install:
	python3 -m pip install $(INSOPT) -e . $(I)

uninstall:
	python3 -m pip uninstall $(INSOPT) fdi  $(I)

PNSDIR=~/pns
installpns:
	mkdir -p $(PNSDIR)
	$(MAKE) uninstallpns
	for i in init run config clean; do \
	  cp fdi/pns/resources/$${i}PTS.ori  $(PNSDIR); \
	  ln -s $(PNSDIR)/$${i}PTS.ori $(PNSDIR)/$${i}PTS; \
	done; \
	mkdir $(PNSDIR)/input $(PNSDIR)/output
	if id -u apache > /dev/null 2>&1; then \
	chown apache $(PNSDIR) $(PNSDIR)/*PTS.ori $(PNSDIR)/input $(PNSDIR)/output; \
	chgrp apache $(PNSDIR) $(PNSDIR)/*PTS* $(PNSDIR)/input $(PNSDIR)/output; \
	fi

uninstallpns:
	for i in init run config clean; do \
	  rm -f $(PNSDIR)/$${i}PTS* $(PNSDIR)/$${i}PTS.ori*; \
	done; \
	rm -f $(PNSDIR)/.lock $(PNSDIR)/hello.out || \
	sudo rm -f $(PNSDIR)/.lock $(PNSDIR)/hello.out

PYREPO	= pypi
INDURL	= 
#PYREPO	= testpypi
#INDURL	= --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/
upload:
	python3 setup.py sdist bdist_wheel
	twine check dist/*
	python3 -m twine upload --repository $(PYREPO) dist/*

testrepo:
	rm -rf /tmp/fditestvirt
	virtualenv -p python3 /tmp/fditestvirt
	. /tmp/fditestvirt/bin/activate && \
	python3 -m pip uninstall -q -q -y fdi ;\
	python3 -m pip cache remove -q -q -q fdi ;\
	python3 -m pip install $(INDURL) "fdi[DEV,SERV]" && \
	echo Testing newly installed fdi ... ; \
	python3 -c 'import sys, fdi.dataset.dataset as f; a=f.ArrayDataset(data=[4,3]); sys.exit(0 if a[1] == 3 else a[1])' && \
	deactivate

reqs:
	pipreqs --ignore tmp --force --savepath requirements.txt.pipreqs

# update _version.py and tag based on setup.py
# VERSION	= $(shell python -S -c "from setuptools_scm import get_version;print(get_version('.'))")
# @ echo update _version.py and tag to $(VERSION)


VERSIONFILE	= fdi/_version.py
VERSION	= $(shell python -S -c "_l = {};f=open('$(VERSIONFILE)'); exec(f.read(), None, _l); f.close; print(_l['__version__'])")

versiontag:
	@ echo  __version__ = \"$(VERSION)\" in $(VERSIONFILE)
	#git tag  $(VERSION)


TESTLOG	= /tmp/fdi-tests.log

OPT	= -r P --log-file=$(TESTLOG) -v -l --pdb
T	= 
test: test1 test2

testpns: test5 test4

testhttp: test6 test7 test8

test1: 
	pytest $(OPT) $(T) tests/test_dataset.py

test2:
	pytest $(OPT) $(T) tests/test_pal.py -k 'not _http'

test3:
	pytest  $(OPT) -k 'server' $(T) tests/test_pns.py

test4:
	pytest $(OPT) -k 'not server' $(T) tests/test_pns.py

test5:
	pytest  $(OPT) $(T) tests/test_utils.py

test6:
	pytest $(OPT) $(T) tests/test_httppool.py

test7:
	pytest $(OPT) $(T) tests/test_httpclientpool.py

test8:
	pytest $(OPT) $(T) tests/test_pal.py -k '_http'


FORCE:

PLOTDIR	= $(SDIR)/_static
plots: plotall plot_dataset plot_pal plot_pns

plotall:
	pyreverse -o png -p all fdi/dataset fdi/pal fdi/pns fdi/utils
	mv classes_all.png packages_all.png $(PLOTDIR)

qplot_%: FORCE
	pyreverse -o png -p $@ fdi/$@
	mv classes_$@.png packages_$@.png $(PLOTDIR)


plot_dataset:
	pyreverse -o png -p dataset fdi/dataset
	mv classes_dataset.png packages_dataset.png $(PLOTDIR)

plot_pal:
	pyreverse -o png -p pal fdi/pal
	mv classes_pal.png packages_pal.png $(PLOTDIR)

plot_pns:
	pyreverse -o png -p pns fdi.pns
	mv classes_pns.png packages_pns.png $(PLOTDIR)

DOCSDIR	= docs
SDIR = $(DOCSDIR)/sphinx
APIOPT	= -T -M --ext-viewcode
APIOPT	= -M --ext-viewcode

docs: docs_api docs_plots docs_html

docs_api:
	rm -rf $(SDIR)/api/fdi
	mkdir -p  $(SDIR)/api/fdi
	sphinx-apidoc $(APIOPT) -o $(SDIR)/api/fdi fdi

docs_plots:
	rm  $(PLOTDIR)/classes*.png $(PLOTDIR)/packages*.png ;\
	make plots

docs_html:
	cd $(SDIR) && make html

