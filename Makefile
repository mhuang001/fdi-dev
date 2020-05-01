PRODUCT = Product
PYDIR	= fdi/dataset
D_RESOURCES= $(PYDIR)/resources
YAML	= $(D_RESOURCES)/$(PRODUCT).yml
TEMPLATE	= $(D_RESOURCES)/$(PRODUCT).template

py: $(YAML) $(TEMPLATE)
	cp $(D_RESOURCES)/product.py.save $(PYDIR)/products.py
	python3 -m fdi.dataset.yaml2python -y $(YAML) -t $(TEMPLATE) -o $(PYDIR)

TESTLOG	= tests/log
OPT	= --debug -v -r P 
OPT	= -r P --log-file=$(TESTLOG)
T	= 
S	=

.PHONY: runserver \
	test test1 test2 test3 test4 \
	plots plot_all plot_dataset plot_pal plot_pns \
	docs doc_api doc_plots doc_html

# default username and password are in pnsconfig.py
runserver:
	python3.6 -m fdi.pns.runflaskserver --username=foo --password=bar -v $(S)


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

