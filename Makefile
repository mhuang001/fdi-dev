PYEXE	= python3

info:
	$(PYEXE) -c "import sys; print('sys.hash_info.width', sys.hash_info.width)"

PRODUCT = Product
B_PRODUCT = BaseProduct
PYDIR	= fdi/dataset
RESDIR	= $(PYDIR)/resources
P_PY	= $(shell $(PYEXE) -S -c "print('$(PRODUCT)'.lower())").py
B_PY	= $(shell $(PYEXE) -S -c "print('$(B_PRODUCT)'.lower())").py
B_INFO	= $(B_PY)
P_YAML	= $(RESDIR)/$(PRODUCT).yml
B_YAML	= $(RESDIR)/$(B_PRODUCT).yml
P_TEMPLATE	= $(RESDIR)
B_TEMPLATE	= $(RESDIR)

py: $(PYDIR)/$(B_PY) $(PYDIR)/$(P_PY)

$(PYDIR)/$(P_PY): $(PYDIR)/yaml2python.py $(P_YAML) $(P_TEMPLATE)/$(PRODUCT).template $(PYDIR)/$(B_PY)
	$(PYEXE) -m fdi.dataset.yaml2python -y $(RESDIR) -t $(P_TEMPLATE) -o $(PYDIR) $(Y)


$(PYDIR)/$(B_PY): $(PYDIR)/yaml2python.py $(B_YAML) $(B_TEMPLATE)/$(B_PRODUCT).template 
	$(PYEXE) -m fdi.dataset.yaml2python -y $(RESDIR) -t $(P_TEMPLATE) -o $(PYDIR) $(Y)

yamlupgrade: 
	$(PYEXE) -m fdi.dataset.yaml2python -y $(RESDIR) -u


.PHONY: runserver runpoolserver reqs install uninstall vtag FORCE \
	test test1 test2 test3 test4 test5\
	plots plotall plot_dataset plot_pal plot_pns \
	docs docs_api docs_plots docs_html

# extra option for 'make runserver S=...'
S	=
# default username and password are in pnsconfig.py
runserver:
	$(PYEXE) -m fdi.pns.runflaskserver --username=foo --password=bar -v $(S)
runpoolserver:
	$(PYEXE) -m fdi.pns.runflaskserver --username=foo --password=bar -v --server=httppool_server $(S)

INSOPT  =
install:
	$(PYEXE) -m pip install $(INSOPT) -e .$(EXT) $(I)

uninstall:
	$(PYEXE) -m pip uninstall $(INSOPT) fdi  $(I)

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
	$(PYEXE) setup.py sdist bdist_wheel
	twine check dist/*
	check-wheel-contents dist
upload:
	$(PYEXE) -m twine upload --repository $(PYREPO) dist/*

wheeltest:
	rm -rf /tmp/fditestvirt
	virtualenv -p $(PYEXE) /tmp/fditestvirt
	. /tmp/fditestvirt/bin/activate && \
	$(PYEXE) -m pip uninstall -q -q -y fdi ;\
	$(PYEXE) -m pip cache remove -q -q -q fdi ;\
	$(PYEXE) -m pip install $(LOCAL_INDURL) "fdi" && \
	$(PYEXE) -m pip show fdi && \
	echo Testing newly installed fdi ... ; \
	$(PYEXE) -c 'import sys, fdi.dataset.dataset as f; a=f.ArrayDataset(data=[4,3]); sys.exit(0 if a[1] == 3 else a[1])' && \
	$(PYEXE) -c 'import sys, pkgutil as p; sys.stdout.buffer.write(p.get_data("fdi", "dataset/resources/Product.template")[:100])' && \
	deactivate

testw:
	rm -rf /tmp/fditestvirt
	virtualenv -p $(PYEXE) /tmp/fditestvirt
	. /tmp/fditestvirt/bin/activate && \
	$(PYEXE) -m pip uninstall -q -q -y fdi ;\
	$(PYEXE) -m pip cache remove -q -q -q fdi ;\
	$(PYEXE) -m pip install $(INDURL) "fdi==1.0.6" && \
	echo Testing newly installed fdi ... ; \
	$(PYEXE) -c 'import sys, fdi.dataset.dataset as f; a=f.ArrayDataset(data=[4,3]); sys.exit(0 if a[1] == 3 else a[1])' && \
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
# VERSION	= $(shell $(PYEXE) -S -c "from setuptools_scm import get_version;print(get_version('.'))")
# @ echo update _version.py and tag to $(VERSION)


VERSIONFILE	= fdi/_version.py
VERSION	= $(shell $(PYEXE) -S -c "_l = {};f=open('$(VERSIONFILE)'); exec(f.read(), None, _l); f.close; print(_l['__version__'])")

versiontag:
	@ echo  version = \"$(VERSION)\" in $(VERSIONFILE)
	git tag  $(VERSION)
	git push origin $(VERSION)

PYTEST	= python3 -m pytest
TESTLOG	= /tmp/fdi-tests.log

OPT	= -r P -v -l --pdb  #--log-file=$(TESTLOG)
T	= 
test: test1 test2

testpns: test5 test4

testhttp: test6 test7 test8

test1: 
	$(PYTEST) tests/test_dataset.py --cov=fdi/dataset $(OPT) $(T)

test2:
	$(PYTEST) tests/test_pal.py -k 'not _http' $(T) --cov=fdi/pal $(OPT)

test3:
	$(PYTEST)  $(OPT) -k 'server' $(T) tests/test_pns.py --cov=fdi/pns

test4:
	$(PYTEST) $(OPT) -k 'not server' $(T) tests/test_pns.py --cov=fdi/pns

test5:
	$(PYTEST)  $(OPT) $(T) tests/test_utils.py --cov=fdi/utils

test6:
	$(PYTEST) $(OPT) $(T) tests/test_httppool.py

test7:
	$(PYTEST) $(OPT) $(T) tests/test_httpclientpool.py

test8:
	$(PYTEST) $(OPT) $(T) tests/test_pal.py -k '_http'


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

########
SERVER_NAME        =httppool_server
PORT        =9884
EXTPORT =$(PORT)
IMAGE_NAME         =httppool_server:v2
IP_ADDR     =10.0.10.114
DOCKERFILE              =fdi/pns/resources/httppool_server.docker

build_server:
	docker build -t $(IMAGE_NAME) --build-arg IP_ADDR=$(IP_ADDR) --build-arg PORT=$(PORT) --build-arg fd=$(fd) --build-arg  re=$(re) -f $(DOCKERFILE) $(D) .

launch_server:
	docker run -d -it --env IP_ADDR=$(IP_ADDR) --env PORT=$(PORT) -p $(PORT):$(EXTPORT) --name $(SERVER_NAME) $(D) $(IMAGE_NAME) $(B)
	sleep 2
	docker ps -n 1

rm_server:
	docker stop $(SERVER_NAME)  || echo not running
	docker  rm $(SERVER_NAME)

rm_serveri:
	docker stop $(SERVER_NAME)  || echo not running
	docker  rm $(SERVER_NAME) || echo go on ...
	docker image rm $(IMAGE_NAME)

B       =/bin/bash
it:
	docker exec -it $(D) $(SERVER_NAME) $(B)

its:
	docker exec -it $(D) $(SERVER_NAME) /bin/bash
