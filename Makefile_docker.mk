PYEXE	= python3

########
DKRREPO	= mhastro
DOCKER_NAME	= fdi
DOCKER_VERSION   =$(shell if [ -f docker_version ]; then cat docker_version; fi)
DFILE	=dockerfile

SERVER_NAME      =httppool
SERVER_VERSION	= $(DOCKER_VERSION)
SFILE	= fdi/httppool/resources/httppool_server.docker

PORT        =9884
SECFILE = $${HOME}/.secret
EXTPORT =$(PORT)
IP_ADDR     =10.0.10.114
PROJ_DIR	= /var/www/httppool_server
SERVER_POOLPATH	= $(PROJ_DIR)/data
LOGGING_LEVEL	=10

LATEST	=im:latest
B       =/bin/bash

FORCE:

docker_version: FORCE
	date +v%y%m%d_%H%M >| docker_version

build_docker:
	@echo Building $(DOCKER_VERSION)
	DOCKER_BUILDKIT=1 docker build -t $(DOCKER_NAME):$(DOCKER_VERSION) \
	--secret id=envs,src=$(SECFILE) \
	--build-arg fd=$(fd) \
	--build-arg  re=$(re) \
	--build-arg DOCKER_VERSION=$(DOCKER_VERSION) \
	-f $(DFILE) \
	$(D) --progress=plain .
	docker tag $(DOCKER_NAME):$(DOCKER_VERSION) $(LATEST)

launch_docker:
	docker run -dit --network=bridge --env-file $(SECFILE) --name $(DOCKER_NAME) $(D) $(LATEST) $(LAU)

build_server:
	DOCKER_BUILDKIT=1 docker build -t $(SERVER_NAME):$(SERVER_VERSION) \
	--secret id=envs,src=$(SECFILE) \
	--build-arg PROJ_DIR=$(PROJ_DIR) \
	--build-arg fd=$(fd) \
	--build-arg  re=$(re) \
	--build-arg SERVER_VERSION=$(SERVER_VERSION) \
	-f $(SFILE) \
	$(D) --progress=plain .
	docker tag $(SERVER_NAME):$(SERVER_VERSION) $(LATEST)

launch_server:
	SN=$(SERVER_NAME)$$(date +'%s') && \
	docker run -dit --network=bridge \
	--mount source=httppool,target=$(SERVER_POOLPATH) \
	--mount source=log,target=/var/log \
	--env-file $(SECFILE) \
	-p $(PORT):$(EXTPORT) \
	-e HOST_PORT=$(PORT) \
	-e LOGGING_LEVEL=$(LOGGING_LEVEL) \
	--name $$SN $(D) $(LATEST) $(LAU)
	sleep 2
	#docker inspect $$SN
	docker ps -n 1

launch_test_server:
	docker tag $(SERVER_NAME):$(SERVER_VERSION) $(LATEST)
	$(MAKE) launch_server PORT=9885 EXTPORT=9885 LOGGING_LEVEL=10 #LATEST=mhastro/httppool

rm_docker:
	cid=`docker ps -a|grep $(LATEST) | awk '{print $$1}'` &&\
	echo Gracefully shutdown server ... 10sec ;\
	if docker stop $$cid; then docker  rm $$cid; else echo NOT running ; fi

rm_dockeri:
	cid=`docker ps -a|grep $(LATEST) | awk '{print $$1}'` &&\
	echo Gracefully shutdown server ... 10sec ;\
	if docker stop $$cid; then docker  rm $$cid; else echo NOT running ; fi
	docker image rm $(LATEST)

it:
	cid=`docker ps -a|grep $(LATEST) | head -n 1 |awk '{print $$1}'` &&\
	if [ -z $$cid ]; then echo NOT running ; false; fi &&\
	docker exec -it $(D) $$cid $(B)

t:
	@ cid=`docker ps -a|grep $(LATEST) | head -n 1 |awk '{print $$1}'` &&\
	if [ -z $$cid ]; then echo NOT running ; false; fi &&\
	docker exec -it $(D) $$cid /usr/bin/tail -n 100 -f /home/apache/error-ps.log
i:
	@ cid=`docker ps -a|grep $(LATEST) | head -n 1 | awk '{print $$1}'` &&\
	if [ -z $$cid ]; then echo NOT running ; false; fi &&\
	docker exec -it $(D) $$cid /usr/bin/less -f /home/apache/error-ps.log

push_docker:
	im=$(DKRREPO)/$(DOCKER_NAME) &&\
	docker tag  $(DOCKER_NAME):$(DOCKER_VERSION) $$im:$(DOCKER_VERSION) &&\
	docker tag  $(DOCKER_NAME):$(DOCKER_VERSION) $$im:latest &&\
	docker push $$im:$(DOCKER_VERSION) &&\
	docker push $$im:latest

push_server:
	im=$(DKRREPO)/$(SERVER_NAME)  &&\
	docker tag  $(SERVER_NAME):$(SERVER_VERSION) $$im:$(SERVER_VERSION) &&\
	docker tag  $(SERVER_NAME):$(SERVER_VERSION) $$im:latest &&\
	docker push $$im:$(SERVER_VERSION) &&\
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
	--mount source=httppool,target=$(SERVER_POOLPATH) \
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
	--mount source=httppool,target=$(SERVER_POOLPATH) \
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

update_docker:
	$(MAKE) install EXT=[DEV,SERV] I=-U &&\
	$(MAKE) docker_version &&\
	$(MAKE) build_docker && $(MAKE) push_docker &&\
	$(MAKE) build_server && $(MAKE) push_server &&\
	$(MAKE) launch_test_server &&\
	$(MAKE) test7 && $(MAKE) test8 &&\
	$(MAKE) rm_docker

