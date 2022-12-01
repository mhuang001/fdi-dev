PYEXE	= python3
LATEST	=im:latest
DKRREPO	= mhastro
DKRREPO = registry.cn-beijing.aliyuncs.com/svom
NETWORK	= host
########
DOCKER_NAME	= fdi
DOCKER_VERSION   =$(shell if [ -f docker_version ]; then cat docker_version; fi)
DFILE	=fdi/dockerfile

ifndef apache
SERVER_NAME      =httppool
API_BASE = $(shell python -m fdi.utils.getconfig api_base)
else
SERVER_NAME      =httppool
API_BASE = $(shell python -m fdi.utils.getconfig api_base)
endif

SERVER_VERSION	= $(DOCKER_VERSION)
ifndef apache
SFILE	= fdi/httppool/resources/httppool_server_uwsgi.docker
else
SFILE	= fdi/httppool/resources/httppool_server.docker
endif

PORT        =9885

ifndef apache
SECFILE = $${HOME}/.secret
else
SECFILE = $${HOME}/.secret
endif

EXTPORT =$(PORT)
IP_ADDR     =0.0.0.0
SERVER_LOCAL_POOLPATH	= /var/www/httppool_server/data
LOGGER_LEVEL	= 10
LOGGER_LEVEL_EXTRAS	= 30

TEST_PORT	= 9885

B       =/bin/bash
D	=

FORCE:

docker_version: FORCE
	date +v%y%m%d_%H%M >| docker_version

# tag the latest
LATEST_NAME	= $(SERVER_NAME)
LATEST_VERSION	= $(SERVER_VERSION)
imlatest:
	docker tag $(LATEST_NAME):$(LATEST_VERSION) $(LATEST)
	docker tag $(LATEST_NAME):$(LATEST_VERSION) $(LATEST_NAME):latest

DOCKERHOME =..
build_docker:
	@echo Building $(DOCKER_VERSION)
	cp docker_version cpfoo; mv -f cpfoo $(DOCKERHOME)/docker_version &&\
	cd $(DOCKERHOME) &&\
	DOCKER_BUILDKIT=1 docker build -t $(DOCKER_NAME):$(DOCKER_VERSION) \
	--network=$(NETWORK) \
	--secret id=envs,src=$(SECFILE) \
	--build-arg fd=$(fd) \
	--build-arg  re=$(re) \
	--build-arg TEST_OPTS='L=10 -r P --setup-show' \
	--build-arg LOGGER_LEVEL=$(LOGGER_LEVEL) \
	--build-arg LOGGER_LEVEL_EXTRAS=$(LOGGER_LEVEL_EXTRAS) \
	--build-arg DOCKER_VERSION=$(DOCKER_VERSION) \
	-f $(DFILE) \
	$(D) --progress=plain .
	$(MAKE) imlatest LATEST_NAME=$(DOCKER_NAME)

launch_docker:
	docker run -dit --network=$(NETWORK) --env-file $(SECFILE) --name $(DOCKER_NAME) $(D) $(DOCKER_NAME):latest $(LAU)

build_server:
	DOCKER_BUILDKIT=1 docker build -t $(SERVER_NAME):$(SERVER_VERSION) \
	--network=$(NETWORK) \
	--secret id=envs,src=$(SECFILE) \
	--build-arg SERVER_LOCAL_POOLPATH=$(SERVER_LOCAL_POOLPATH) \
	--build-arg fd=$(fd) \
	--build-arg re=$(re) \
	--build-arg TEST_OPTS='L=10 T="-r P --setup-show"' \
	--build-arg SERVER_VERSION=$(SERVER_VERSION) \
	--build-arg API_BASE=$(API_BASE) \
	-f $(SFILE) \
	$(D) --progress=plain .
	$(MAKE) imlatest LATEST_NAME=$(SERVER_NAME)

# run im:latest
launch_server:
	SN=$(SERVER_NAME)$$(date +'%s') && \
	docker run -dit --network=$(NETWORK) \
	--mount source=httppool,target=$(SERVER_LOCAL_POOLPATH) \
	--mount source=log,target=/var/log_mounted \
	--env-file $(SECFILE) \
	-p $(PORT):$(EXTPORT) \
	-e PNS_HOST_PORT=$(PORT) \
	-e PNS_LOGGER_LEVEL=$(LOGGER_LEVEL) \
	-e PNS_LOGGER_LEVEL_EXTRAS=$(LOGGER_LEVEL_EXTRAS) \
	-e PNS_API_BASE=$(API_BASE) \
	--name $$SN $(D) $(LATEST) $(LAU) ;\
	docker ps -n 1
	#if [ $$? -gt 0 ]; then echo *** Launch failed; false; else \
	sleep 2 ;\
	#docker inspect $$SN ;\

launch_test_server:
	$(MAKE) imlatest LATEST_NAME=$(SERVER_NAME)
	$(MAKE) launch_server PORT=$(TEST_PORT) EXTPORT=$(TEST_PORT) LOGGER_LEVEL=$(LOGGER_LEVEL) LOGGER_LEVEL_EXTRAS=$(LOGGER_LEVEL_EXTRAS) #LATEST=mhastro/httppool

rm_docker:
	cids=`docker ps -a|grep $(LATEST) | awk '{print $$1}'` &&\
	echo Gracefully shutdown server ... 10sec ;\
	for cid in $$cids; do echo rm $$cid ...; \
	if docker stop $$cid; then docker  rm $$cid; else echo NOT running ; fi ;\
	done

rm_dockeri:
	cid=`docker ps -a|grep $(LATEST) | awk '{print $$1}'` &&\
	echo Gracefully shutdown server ... 10sec ;\
	if docker stop $$cid; then docker  rm $$cid; else echo NOT running ; fi
	docker image rm $(LATEST)

it:
	cid=`docker ps -a|grep $(LATEST) | head -n 1 |awk '{print $$1}'` &&\
	if [ -z $$cid ]; then echo NOT running ; false; fi &&\
	echo $$cid ... && docker exec -it $(D) $$cid $(B)

t:
	@ cid=`docker ps -a|grep $(LATEST) | head -n 1 |awk '{print $$1}'` &&\
	if [ -z $$cid ]; then echo NOT running ; false; fi &&\
	docker exec -it $(D) $$cid /usr/bin/tail -n 100 -f /var/log/uwsgi/uwsgi.log
i:
	@ cid=`docker ps -a|grep $(LATEST) | head -n 1 | awk '{print $$1}'` &&\
	if [ -z $$cid ]; then echo NOT running ; false; fi &&\
	docker exec -it $(D) $$cid /usr/bin/less -f /var/log/uwsgi/uwsgi/uwsgi.log

PUSH_NAME	= $(SERVER_NAME)
PUSH_VERSION	= $(SERVER_VERSION)
push_d:
	im=$(DKRREPO)/$(PUSH_NAME) &&\
	docker tag  $(PUSH_NAME):$(PUSH_VERSION) $$im:$(PUSH_VERSION) &&\
	docker tag  $(PUSH_NAME):$(PUSH_VERSION) $$im:latest  &&\
	docker push $$im:$(PUSH_VERSION) &&\
	docker push $$im:latest

vol:
	docker volume create httppool
	docker volume create log
	docker volume inspect httppool log

pull_server:
	im=$(DKRREPO)/$(SERVER_NAME)  &&\
	docker pull $$im:latest &&\
	docker tag  $$im:latest im:latest

backup_server:
	f=backup_$(SERVER_NAME)_$(SERVER_VERSION)_`date +'%y%m%dT%H%M%S' --utc`.tar &&\
	echo Backup file: $$f ;\
	docker run -it --rm \
	--mount source=httppool,target=$(SERVER_LOCAL_POOLPATH) \
	--mount source=log,target=/var/log \
	--env-file $(SECFILE) \
	-p 9883:9883 \
	-a stdin -a stdout \
	--entrypoint "" \
	--name $(SERVER_NAME)_backup $(D) $(SERVER_NAME):$(SERVER_VERSION)  \
	/bin/bash -c 'cd $(PROJ_DIR)/data && tar cf /dev/stdout .' >  $$f

restore_server:
ifndef from
	echo Must give filename: $(MAKE) restare_server from=filename
else
	echo Restore from backup file: $(from)
	cat $(from) | docker run -i --rm \
	--mount source=httppool,target=$(SERVER_LOCAL_POOLPATH) \
	--mount source=log,target=/var/log \
	--env-file $(SECFILE) \
	-p 9883:9883 \
	-a stdin -a stdout \
	--entrypoint "" \
	--name $(SERVER_NAME)_backup $(D) $(SERVER_NAME):$(SERVER_VERSION)  \
	/bin/bash -c 'cd $(PROJ_DIR)/data && tar xvf - .'
endif

restore_test:
	$(MAKE) rm_docker
	docker volume prune --force && 	docker volume ls
	@echo %%% above should be empty %%%%%%%
	$(MAKE) launch_server && $(MAKE) it B='/bin/ls -l $(PROJ_DIR)/data'
	@echo %%% above should be empty %%%%%%%
	$(MAKE) restore_server from=backup_httppool_v5_210722T015659.tar
	$(MAKE) it B='/bin/ls -l $(PROJ_DIR)/data'
	@echo %%% above should NOT be empty %%%%%%%


PIPCACHE=../fdi/pipcache
PIPWHEELS=../fdi/wheels
update_docker:
	(\
	$(MAKE) rm_docker &&\
	$(MAKE) docker_version &&\
	python3 -m pip wheel --disable-pip-version-check --cache-dir $(PIPCACHE) --wheel-dir $(PIPWHEELS) -e .[DEV,SERV,SCI] &&\
	python3 -m pip install $(PIPOPT) --no-index -f $(PIPWHEELS) -e .[DEV,SERV,SCI] &&\
	$(MAKE) build_docker && $(MAKE) push_d PUSH_NAME=$(DOCKER_NAME) &&\
	$(MAKE) build_server && $(MAKE) push_d PUSH_NAME=$(SERVER_NAME) &&\
	$(MAKE) launch_test_server &&\
	$(MAKE) test7 && $(MAKE) test8 &&\
	$(MAKE) rm_docker ) 2>&1 | tee update.log
	@echo Done. `cat docker_version`

cleanup:
	docker rmi -f `docker images -a|grep pool|awk 'BEGIN{FS=" "}{print $3}'`
	docker rmi -f `docker images -a|grep csc |awk 'BEGIN{FS=" "}{print $3}'`
	docker rmi -f `docker images -a|grep m/fdi|awk 'BEGIN{FS=" "}{print $3}'`

PIPCACHE=~/csc38/fdi/pipcache
PIPWHEELS=~/csc38/fdi/wheels
stage:
	python3.8 -m pip wheel --disable-pip-version-check --cache-dir $(PIPCACHE) --wheel-dir $(PIPWHEELS) pip>=21 wheel setuptools &&\
	python3.8 -m pip wheel --disable-pip-version-check --cache-dir $(PIPCACHE) --wheel-dir $(PIPWHEELS) -e .[DEV,SERV,SCI]
