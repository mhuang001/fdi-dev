PYEXE	= python3

info:
	$(PYEXE) -c "import sys, time; print('sys.hash_info.width', sys.hash_info.width, 'epoch', time.gmtime(0))"
####
TO_UPPER    = $(shell python -c "print('$(1)'.upper())")
TO_LOWER    = $(shell python -c "print('$(1)'.lower())")

PRODUCT = Product
B_PRODUCT = BaseProduct
PYDIR	:= fdi/dataset
RESDIR	:= $(PYDIR)/resources
P_PY	= $(call TO_LOWER,$(PRODUCT)).py
B_PY	= $(call TO_LOWER,$(B_PRODUCT)).py
B_INFO	= $(B_PY)
P_YAML	= $(RESDIR)/$(PRODUCT).yml
B_YAML	= $(RESDIR)/$(B_PRODUCT).yml
P_TEMPLATE	:= $(RESDIR)/$(PRODUCT).template
B_TEMPLATE	:= $(RESDIR)/$(B_PRODUCT).template

DSETS = ArrayDataset_DataModel TableDataset_DataModel UnstructuredDataset_DataModel MediaWrapper_DataModel
DSETS_PY	= $(addsuffix .py,$(call TO_LOWER,$(DSETS)))
DSETS_YAML	= $(foreach y,$(DSETS),$(RESDIR)/$(y).yml)
DSETS_TEMPL	= $(foreach y,$(DSETS),$(RESDIR)/$(y).template)
DSETSpy		= $(addprefix $(PYDIR)/,$(DSETS_PY))

# BaseProduct, Product and datasets
py: $(PYDIR)/$(B_PY) $(PYDIR)/$(P_PY) $(DSETSpy)

$(DSETSpy): $(PYDIR)/yaml2python.py $(DSETS_YAML) $(DSETS_TEMPL) $(PYDIR)/$(B_PY)
	$(PYEXE) -m fdi.dataset.yaml2python -y $(RESDIR) -t $(RESDIR) -o $(PYDIR) $(Y)

$(PYDIR)/$(P_PY): $(PYDIR)/yaml2python.py $(P_YAML) $(P_TEMPLATE) $(PYDIR)/$(B_PY)
	$(PYEXE) -m fdi.dataset.yaml2python -y $(RESDIR) -t $(RESDIR) -o $(PYDIR) $(Y)


$(PYDIR)/$(B_PY): $(PYDIR)/yaml2python.py $(B_YAML) $(B_TEMPLATE) 
	$(PYEXE) -m fdi.dataset.yaml2python -y $(RESDIR) -t $(RESDIR) -o $(PYDIR) $(Y)

yamlupgrade: 
	$(PYEXE) -m fdi.dataset.yaml2python -y $(RESDIR) -u


.PHONY: runserver runpoolserver reqs install uninstall vtag FORCE \
	test test1 test2 test3 test4 test5\
	plots plotall plot_dataset plot_pal plot_pns \
	docs docs_api docs_plots docs_html \
	pipfile

# extra option for 'make runserver S=...'
S	=
# default username and password are in pnsconfig.py
runserver:
	$(PYEXE) -m fdi.pns.runflaskserver $(S)
runpoolserver:
	$(PYEXE) httppool_app.py --server=httppool_server $(S)

EXT	=
PKGS	= requests filelock ruamel.yaml tabulate paho-mqtt
PKGSDEV	=pytest pytest-cov aiohttp Flask Flask_HTTpAuth
PKGSDEP	= waitress twine sphinx_rtd_theme sphinx-copybutton

PIPOPT  = --disable-pip-version-check --no-color
install:
	$(PYEXE) -m pip install $(PIPOPT) -e .$(EXT) $(I)

uninstall:
	$(PYEXE) -m pip uninstall $(PIPOPT) fdi  $(I)

addsubmodule:
	git submodule add  --name leapseconds https://gist.github.com/92df922103ac9deb1a05 ext/leapseconds

update:
	git submodule update --init --recursive --remote

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

virtest:
	rm -rf /tmp/fditestvirt
	virtualenv -p $(PYEXE) /tmp/fditestvirt
	. /tmp/fditestvirt/bin/activate && \
	$(PYEXE) -m pip uninstall -q -q -y fdi ;\
	$(PYEXE) -m pip cache remove -q -q -q fdi ;\
	$(PYEXE) -m pip install $(LOCAL_INDURL) "fdi" && \
	$(PYEXE) -m pip show fdi && \
	echo Testing newly installed fdi ... ; \
	$(PYEXE) -c 'import sys, fdi.dataset.arraydataset as f; a=f.ArrayDataset(data=[4,3]); sys.exit(0 if a[1] == 3 else a[1])' && \
	$(PYEXE) -c 'import sys, pkgutil as p; sys.stdout.buffer.write(p.get_data("fdi", "dataset/resources/Product.template")[:100])' && \
	deactivate

J_OPTS	= ${JAVA_OPTS} -XX:MaxPermSize=256M -Xmx1024M -DloggerPath=conf/log4j.properties
J_OPTS	= ${JAVA_OPTS} -Xmx1024M -DloggerPath=conf/log4j.properties
VERYOLD	=-t ../swagger-codegen/modules/swagger-codegen/src/main/resources/flaskConnexion
FCTEMPL	=../swagger-codegen-generators/src/main/resources/handlebars/pythonFlaskConnexion/
AGS	=  -vv
SWJAR	= ../swagger-codegen/swagger-codegen-cli-3.0.25.jar
# The one below is not working probably because mvn is not working
#SWJAR	= ../swagger-codegen/modules/swagger-codegen-cli/target/swagger-codegen-cli.jar

SCHEMA_DIR	=fdi/httppool/schema
# so that flsgger can understand.
de-ref:
	swagger-cli bundle  -t yaml ${SCHEMA_DIR}/pools.yml -o ${SCHEMA_DIR}/pools_resolved.yml

# make swagger server subs
api:
	rm -rf fdi/httppool/flaskConnexion/*
	java $(J_OPTS) -jar $(SWJAR) generate $(AGS) -i ./fdi/httppool/schema/pools.yml -l python-flask -o ./fdi/httppool/swagger -Dservice -DpackageName=fdi.httppool.swagger -DpackageVersion=2.0 -DserverPort=9000

# $ref: works, unlike swagger editor
watchapi:
	swagger-ui-watcher fdi/httppool/schema/pools.yml

swagger-editor:
	@echo browser open file:///d:/code/swagger-editor/index.html
reqs:
	pipreqs --ignore tmp --force --savepath requirements.txt.pipreqs

gitadd:
	git add LICENSE README.rst CHANGELOG.rst setup.py MANIFEST.in \
	.gitignore noxfile.py Makefile .gitmodules .gitlab-ci.yml \
	.readthedocs.yml .dockerignore CONTRIBUTORS
	git add bin/reinstall bin/installpns bin/update
	git add resources
	git add fdi/*.py
	git add fdi/dataset/*.py fdi/dataset/resources
	git add fdi/pns/*.py fdi/pns/resources
	git add fdi/pal/*.py fdi/pal/resources
	git add fdi/utils/*.py
	git add httppool_app.py fdi/httppool
	git add Makefile_tests.mk tests/*.py tests/resources tests/serv/*.py tests/serv/resources
	git add Makefile_docs.mk docs/sphinx/index.rst docs/sphinx/usage docs/sphinx/api \
	docs/sphinx/conf.py docs/sphinx/Makefile \
	docs/sphinx/_static docs/sphinx/_templates
	git add Makefile_docker.mk dockerfile dockerfile_entrypoint.sh
# update _version.py and tag based on setup.py
# VERSION	= $(shell $(PYEXE) -S -c "from setuptools_scm import get_version;print(get_version('.'))")
# @ echo update _version.py and tag to $(VERSION)


VERSIONFILE	= fdi/_version.py
VERSION	= $(shell $(PYEXE) -S -c "_l = {};f=open('$(VERSIONFILE)'); exec(f.read(), None, _l); f.close; print(_l['__version__'])")

vtag:
	@ echo  version = \"$(VERSION)\" in $(VERSIONFILE)
	git tag  $(VERSION)
	git push origin $(VERSION)

FORCE:

include Makefile_tests.mk
include Makefile_docs.mk

########
# docker
########

include Makefile_docker.mk

