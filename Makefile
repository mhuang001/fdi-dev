PRODUCT = Product
B_PRODUCT = BaseProduct
PYDIR	= fdi/dataset
RESDIR	= $(PYDIR)/resources
P_PY	= $(shell python -c "print('$(PRODUCT)'.lower())").py
B_PY	= $(shell python -c "print('$(B_PRODUCT)'.lower())").py
B_INFO	= $(B_PY)
P_YAML	= $(RESDIR)/$(PRODUCT).yml
B_YAML	= $(RESDIR)/$(B_PRODUCT).yml
P_TEMPLATE	= $(RESDIR)/$(PRODUCT).template
B_TEMPLATE	= $(RESDIR)/$(B_PRODUCT).template

py: $(PYDIR)/$(B_PY) $(PYDIR)/$(P_PY)

$(PYDIR)/$(P_PY): $(PYDIR)/yaml2python.py $(P_YAML) $(P_TEMPLATE) $(PYDIR)/$(B_PY)
	cp $(RESDIR)/product.py.save $(PYDIR)/$(P_PY)
	python3 -m fdi.dataset.yaml2python -y $(P_YAML) -t $(P_TEMPLATE) -o $(PYDIR)


# only the productInfo and __init__() kwds are generated in $(RESDIR).
# $(RESDIR)/$(B_INFO) must be manually integrated into $(PYDIR)/$(B_PY). 

$(RESDIR)/$(B_INFO): $(PYDIR)/yaml2python.py $(B_YAML) $(B_TEMPLATE)
	python3 -m fdi.dataset.yaml2python -y $(B_YAML) -t $(B_TEMPLATE) -o $(RESDIR)

$(PYDIR)/$(B_PY): $(RESDIR)/$(B_INFO)
	@echo $(RESDIR)/$(B_INFO) is NEWER than $(PYDIR)/$(B_PY). \
	It must be manually integrated into $(PYDIR)/$(B_PY).
	@ echo Re-run make after editing. Exiting... ; exit


TESTLOG	= tests/log
OPT	= --debug -v -r P 
OPT	= -r P --log-file=$(TESTLOG)
T	= 
S	=

.PHONY: runserver reqs\
	test test1 test2 test3 test4 \
	plots plot_all plot_dataset plot_pal plot_pns \
	docs doc_api doc_plots doc_html

# default username and password are in pnsconfig.py
runserver:
	python3.6 -m fdi.pns.runflaskserver --username=foo --password=bar -v $(S)


reqs:
	pipreqs --ignore tmp --force --savepath requirements.txt.pipreqs

test: test1 test2 test3 test4

test1: 
	pytest $(OPT) $(T) tests/test_dataset.py

test2:
	pytest $(OPT) $(T) tests/test_pal.py

test3:
	pytest $(OPT) $(T) tests/test_pns.py

test4:
	pytest  $(OPT) -k 'server' $(T) tests/test_pns.py

plots: plot_all plot_dataset plot_pal plot_pns

plot_all:
	pyreverse -o png -p all fdi/dataset fdi/pal fdi/pns fdi/utils
	mv classes_all.png packages_all.png resources

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

PLOTSET	= dataset pal pns
p: resources/classes_$(PLOTSET).png resources/packages_$(PLOTSET).png

classes_%.png packages_%.png :
	pyreverse -o png -p $@ fdi/$@
	mv classes_$@.png packages_$@.png resources

