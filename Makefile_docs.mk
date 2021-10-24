
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
