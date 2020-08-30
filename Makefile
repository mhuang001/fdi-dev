PRODUCT = Product
B_PRODUCT = BaseProduct
PYDIR	= fdi/dataset
RESDIR	= $(PYDIR)/resources
P_PY	= $(shell python -c "print('$(PRODUCT)'.lower())").py
B_PY	= $(shell python -c "print('$(B_PRODUCT)'.lower())").py
B_INFO	= $(B_PY)
P_YAML	= $(RESDIR)
B_YAML	= $(RESDIR)
P_TEMPLATE	= $(RESDIR)
B_TEMPLATE	= $(RESDIR)

py: $(PYDIR)/$(B_PY) $(PYDIR)/$(P_PY)

$(PYDIR)/$(P_PY): $(PYDIR)/yaml2python.py $(P_YAML) $(P_TEMPLATE)/$(PRODUCT).template $(PYDIR)/$(B_PY)
	python3 -m fdi.dataset.yaml2python -y $(P_YAML) -t $(P_TEMPLATE) -o $(PYDIR)


$(PYDIR)/$(B_PY): $(PYDIR)/yaml2python.py $(B_YAML) $(B_TEMPLATE)/$(B_PRODUCT).template 
	python3 -m fdi.dataset.yaml2python -y $(P_YAML) -t $(P_TEMPLATE) -o $(PYDIR)

yamlupgrade: 
	python3 -m fdi.dataset.yaml2python -y $(P_YAML) -u


.PHONY: runserver reqs install uninstall vtag FORCE \
	test test1 test2 test3 test4 \
	plots plotall plot_dataset plot_pal plot_pns \
	docs doc_api doc_plots doc_html

# extra option for 'make runserver S=...'
S	=
# default username and password are in pnsconfig.py
runserver:
	python3 -m fdi.pns.runflaskserver --username=foo --password=bar -v $(S)

install:
	pip3 install -e .

uninstall:
	pip3 uninstall fdi

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

reqs:
	pipreqs --ignore tmp --force --savepath requirements.txt.pipreqs

# update _version.py and tag based on setup.py
VERSION	= $(shell python -c "from setuptools_scm import get_version;print(get_version('.'))")
versiontag:
	@ echo update _version.py and tag to $(VERSION)
	@ echo  __version__ = \"$(VERSION)\" > fdi/_version.py
	git tag  $(VERSION)

TESTLOG	= tests/log

OPT	= -r P --log-file=$(TESTLOG) -v -l --pdb
T	= 
test: test1 test2 test4 test3

test1: 
	pytest $(OPT) $(T) tests/test_dataset.py

test2:
	pytest $(OPT) $(T) tests/test_pal.py

test3:
	pytest $(OPT) -k 'not server' $(T) tests/test_pns.py

test4:
	pytest  $(OPT) -k 'server' $(T) tests/test_pns.py

plots: plotall plot_dataset plot_pal plot_pns

plotall:
	pyreverse -o png -p all fdi/dataset fdi/pal fdi/pns fdi/utils
	mv classes_all.png packages_all.png resources

qplot_%: FORCE
	pyreverse -o png -p $@ fdi/$@
	mv classes_$@.png packages_$@.png resources

FORCE:


plot_dataset:
	pyreverse -o png -p dataset fdi/dataset
	mv classes_dataset.png packages_dataset.png resources

plot_pal:
	pyreverse -o png -p pal fdi/pal
	mv classes_pal.png packages_pal.png resources

plot_pns:
	pyreverse -o png -p pns fdi/pns
	mv classes_pns.png packages_pns.png resources


DOCDIR	= doc
SDIR = $(DOCDIR)/sphinx
APIOPT	= -T -M --ext-viewcode
APIOPT	= -M --ext-viewcode

docs: doc_api doc_plots doc_html

doc_api:
	rm -rf $(SDIR)/api/fdi
	mkdir -p  $(SDIR)/api/fdi
	sphinx-apidoc $(APIOPT) -o $(SDIR)/api/fdi fdi

doc_plots:
	cd $(SDIR)/_static && \
	rm -f  classes*.png packages*.png ;\
	for i in  ../../../resources/*.png; do  ln -s $$i .; done

doc_html:
	cd $(SDIR) && make html

