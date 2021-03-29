info:
	python -c "import sys; print('sys.hash_info.width', sys.hash_info.width)"

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
	python3 -m pip install $(INSOPT) -e .$(I)

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
	mkdir -p $(PNSDIR)/input $(PNSDIR)/output
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
LOCAL_INDURL	= $(CURDIR)/dist/*.whl --extra-index-url https://pypi.org/simple/
wheel:
	# git ls-tree -r HEAD | awk 'print $4' > MANIFEST
	rm -rf dist/* build *.egg-info
	python3 setup.py sdist bdist_wheel
	twine check dist/*
	check-wheel-contents dist
upload:
	python3 -m twine upload --repository $(PYREPO) dist/*

wheeltest:
	rm -rf /tmp/fditestvirt
	virtualenv -p python3 /tmp/fditestvirt
	. /tmp/fditestvirt/bin/activate && \
	python3 -m pip uninstall -q -q -y fdi ;\
	python3 -m pip cache remove -q -q -q fdi ;\
	python3 -m pip install $(LOCAL_INDURL) "fdi" && \
	python3 -m pip show fdi && \
	echo Testing newly installed fdi ... ; \
	python3 -c 'import sys, fdi.dataset.dataset as f; a=f.ArrayDataset(data=[4,3]); sys.exit(0 if a[1] == 3 else a[1])' && \
	python3 -c 'import sys, pkgutil as p; sys.stdout.buffer.write(p.get_data("fdi", "dataset/resources/Product.template")[:100])' && \
	deactivate

testw:
	rm -rf /tmp/fditestvirt
	virtualenv -p python3 /tmp/fditestvirt
	. /tmp/fditestvirt/bin/activate && \
	python3 -m pip uninstall -q -q -y fdi ;\
	python3 -m pip cache remove -q -q -q fdi ;\
	python3 -m pip install $(INDURL) "fdi==1.0.6" && \
	echo Testing newly installed fdi ... ; \
	python3 -c 'import sys, fdi.dataset.dataset as f; a=f.ArrayDataset(data=[4,3]); sys.exit(0 if a[1] == 3 else a[1])' && \
	deactivate

J_OPTS	= ${JAVA_OPTS} -XX:MaxPermSize=256M -Xmx1024M -DloggerPath=conf/log4j.properties
J_OPTS	= ${JAVA_OPTS} -Xmx1024M -DloggerPath=conf/log4j.properties
AGS	= -t ../swagger-codegen/modules/swagger-codegen/src/main/resources/flaskConnexion -vv
SWJAR	= ../swagger-codegen/swagger-codegen-cli.jar
SWJAR	= ../swagger-codegen/modules/swagger-codegen-cli/target/swagger-codegen-cli.jar
api:
	rm -rf httppool/flaskConnexion/*
	java $(J_OPTS) -jar $(SWJAR) generate $(AGS) -i ./httppool/swagger.yaml -l python-flask -o ./httppool/flaskConnexion -Dservice

reqs:
	pipreqs --ignore tmp --force --savepath requirements.txt.pipreqs

# update _version.py and tag based on setup.py
# VERSION	= $(shell python -S -c "from setuptools_scm import get_version;print(get_version('.'))")
# @ echo update _version.py and tag to $(VERSION)


VERSIONFILE	= fdi/_version.py
VERSION	= $(shell python -S -c "_l = {};f=open('$(VERSIONFILE)'); exec(f.read(), None, _l); f.close; print(_l['__version__'])")

versiontag:
	@ echo  version = \"$(VERSION)\" in $(VERSIONFILE)
	git tag  $(VERSION)
	git push origin $(VERSION)

TESTLOG	= /tmp/fdi-tests.log

OPT	= -r P --log-file=$(TESTLOG) -v -l --pdb 
T	= 
test: test1 test2

testpns: test5 test4

testhttp: test6 test7 test8

test1: 
	pytest tests/test_dataset.py --cov=fdi/dataset $(OPT) $(T)

test2:
	pytest tests/test_pal.py -k 'not _http' $(T) --cov=fdi/pal $(OPT)

test3:
	pytest  $(OPT) -k 'server' $(T) tests/test_pns.py --cov=fdi/pns

test4:
	pytest $(OPT) -k 'not server' $(T) tests/test_pns.py --cov=fdi/pns

test5:
	pytest  $(OPT) $(T) tests/test_utils.py --cov=fdi/utils

test6:
	pytest $(OPT) $(T) tests/test_httppool.py

test7:
	pytest $(OPT) $(T) tests/test_httpclientpool.py

test8:
	pytest $(OPT) $(T) tests/test_pal.py -k '_http'


FORCE:

PLOTDIR	= $(SDIR)/_static
plots: plot_dataset plot_pal plot_pns

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

