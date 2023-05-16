include  Makefile_docker_common.mk

DOCKER_NAME	= fdi
DFILE	=fdi/dockerfile

SERVER_NAME      =httppool
BASEURL = $(shell python -m fdi.utils.getconfig baseurl)
SFILE	= fdi/fdi/httppool/resources/httppool_server_uwsgi.docker

PORT        =9885

SECFILE = $${HOME}/.secret
SECFILE_SERV = $${HOME}/.secret_serv

EXTPORT =$(PORT)
IP_ADDR     =0.0.0.0
SERVER_LOCAL_POOLPATH	= /var/www/httppool_server/data/$(API_VERSION)
LOGGER_LEVEL	= 10
LOGGER_LEVEL_EXTRAS	= 30

TEST_PORT	= 9885

B       =/bin/bash
D	=
DOCKERHOME      =..

FORCE:

MKOPT	=-s -S
fdi_WHEELS	=../wheels
fdi_PIPCACHE	= ../pipcache
fdi_PROJ_PIPCACHE	= $(fdi_PIPCACHE)
FPK	:=fdi
fdi_PIPOPT	=--disable-pip-version-check --cache-dir $(fdi_PROJ_PIPCACHE) -f $(fdi_WHEELS)
fdi_EXT	:="[DEV,SERV,SCI]"
PROJ-INSTALL:
	@echo fdi_EXT=$(fdi_EXT) fdi_PIPOPT=$(fdi_PIPOPT)
ifeq ($(WHEEL_INSTALL), 1)
	@echo "*** MAKE WHEEL $(FPK) ***"
	@echo ----- `pwd`
	rm -f $(fdi_WHEELS)/fdi*
	#make $(MKOPT) uninstall I="$(I)"
	python3 -m pip wheel $(fdi_PIPOPT) --wheel-dir $(fdi_WHEELS) -e .$(fdi_EXT) $(I)
else ifeq ($(WHEEL_INSTALL), 3)
	@echo "*** WHEEL INSTALL $(FPK) ***"
	$(MKPRE) $(PYEXE) -m pip  install $(FPK) $(I) --no-index $(fdi_PIPOPT) 
else ifeq ($(WHEEL_INSTALL), 13)
	@echo "*** MAKE WHEEL $(FPK) ***"
	@echo ----- `pwd`
	rm -f $(fdi_WHEELS)/fdi*
	#make $(MKOPT) uninstall I="$(I)"
	python3 -m pip wheel $(fdi_PIPOPT) --wheel-dir $(fdi_WHEELS) -e .$(fdi_EXT) $(I)
	python3 -m pip install -e .$(fdi_EXT) $(fdi_PIPOPT) $(I)
else ifeq ($(WHEEL_INSTALL), 4)
	@echo "*** DEV INSTALL $(FPK) ***"
	@echo ----- `pwd`
	python3 -m pip install -e .$(fdi_EXT) $(fdi_PIPOPT) $(I)
endif
	#rm $(fdi_WHEELS)/fdi* &&\

test_docker:
	cid=`docker ps -a|grep $(LATEST) | awk '{print $$1}'` &&\
	docker exec -it $$cid sh -c '(cd $(DOCKER_NAME); make test)'

test_server:
	cid=`docker ps -a|grep $(LATEST) | awk '{print $$1}'` &&\
	docker exec -it $$cid sh -c '(cd fdi; make testhttp)'

