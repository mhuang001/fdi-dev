PYEXE	:=python3.8
pkg	:=testpackage
site	:=$(shell python3.8 -c "import site; print(' '.join(site.getsitepackages()))") #/site-packages
wheel-tpkg:
	$(PYEXE) -m pip wheel -e . --no-cache -w /tmp -q

install-tpkg: wheel-tpkg
	$(PYEXE) -m pip install $(pkg) --no-index --no-cache -f /tmp

verify-tpkg:
	cd /; $(PYEXE) -c 'import $(pkg)'

clean-tpkg:
	$(PYEXE) -m pip uninstall $(pkg) -y
	if [ -d build ]; then $(PYEXE) setup.py clean --all; fi
	@echo clearing $(pkg) in $(site) 
	for s in $(site); do \
	rm -f $${s}/$(pkg)-nspkg.pth ;\
	rm -f $${s}/$(pkg).*link;\
	rm -rf $${s}/$(pkg); done
	/bin/rm -f /tmp/$(pkg)*.whl
