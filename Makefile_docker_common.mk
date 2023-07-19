
.PHONY: i, t

PYEXE   = python3.8
LATEST  =im:latest
DKRREPO = mhastro
DKRREPO = registry.cn-beijing.aliyuncs.com/svom
NETWORK = host
SSHIDpri = $(HOME)/.ssh/id_rsa
SSHIDpub = $(HOME)/.ssh/id_rsa.pub
########

BASEURL = $(shell python -m fdi.utils.getconfig baseurl)
API_VERSION= $(shell python -m fdi.utils.getconfig api_version)
SERVER_LOCAL_DATAPATH   = /var/www/httppool_server/data
SERVER_LOCAL_POOLPATH   = $(SERVER_LOCAL_DATAPATH)/$(API_VERSION)

docker_version: FORCE
	date +v%y%m%d_%H%M > docker_version
DOCKER_VERSION  = $(shell if [ -f docker_version ]; then cat docker_version; fi)
SERVER_VERSION  = $(DOCKER_VERSION)

# tag the latest
LATEST_NAME	= $(SERVER_NAME)
LATEST_VERSION	= $(SERVER_VERSION)
imlatest:
	docker tag $(LATEST_NAME):$(LATEST_VERSION) $(LATEST)
	docker tag $(LATEST_NAME):$(LATEST_VERSION) $(LATEST_NAME):latest

build_docker:
	@echo Building $(DOCKER_VERSION) $(SECFILE) with $(SSHID)
	cp docker_version cpfoo; mv -f cpfoo $(DOCKERHOME)/docker_version &&\
	cd $(DOCKERHOME) &&\
	DOCKER_BUILDKIT=1 docker build -t $(DOCKER_NAME):$(DOCKER_VERSION) \
	--network=$(NETWORK) \
	--secret id=envs,src=$(SECFILE) \
	--secret id=sshpri,src=$(SSHIDpri) \
	--secret id=sshpub,src=$(SSHIDpub) \
	--build-arg fd=$(fd) \
	--build-arg  re=$(re) \
	--build-arg TEST_OPTS='' \
	--build-arg LOGGER_LEVEL=$(LOGGER_LEVEL) \
	--build-arg LOGGER_LEVEL_EXTRAS=$(LOGGER_LEVEL_EXTRAS) \
	--build-arg DOCKER_VERSION=$(DOCKER_VERSION) \
	-f $(DFILE) \
	$(D) --progress=plain .
	$(MAKE) imlatest LATEST_NAME=$(DOCKER_NAME)
	#--ssh default=$$SSH_AUTH_SOCK,uid=$$(id -u) \
#launch_docker:
#	docker run -dit --network=$(NETWORK) --add-host dev:127.0.0.1 --env-file $(SECFILE) --name $(DOCKER_NAME) $(D) $(DOCKER_NAME):latest $(LAU)

build_server:
	cd $(DOCKERHOME) &&\
	DOCKER_BUILDKIT=1 docker build -t $(SERVER_NAME):$(SERVER_VERSION) \
	--network=$(NETWORK) \
	--secret id=envs,src=$(SECFILE_SERV) \
	--secret id=sshpri,src=$(SSHIDpri) \
	--secret id=sshpub,src=$(SSHIDpub) \
	--build-arg SERVER_LOCAL_POOLPATH=$(SERVER_LOCAL_POOLPATH) \
	--build-arg fd=$(fd) \
	--build-arg re=$(re) \
	--build-arg TEST_T='-r P --setup-show' \
	--build-arg SERVER_VERSION=$(SERVER_VERSION) \
	--build-arg BASEURL=$(BASEURL) \
	-f $(SFILE) \
	$(D) --progress=plain .
	$(MAKE) imlatest LATEST_NAME=$(SERVER_NAME)

# run im:latest
launch_server:
	SN=$(SERVER_NAME)$$(date +'%s') && \
	docker run -d -it --network=$(NETWORK) \
	--mount source=httppool,target=$(SERVER_LOCAL_DATAPATH) \
	--mount source=log,target=/var/log_mounted \
	--env-file $(SECFILE_SERV) \
	--add-host dev:127.0.0.1 \
	-p $(PORT):$(EXTPORT) \
	-e PNS_PORT=$(PORT) \
	-e PNS_SERVER_LOCAL_POOLPATH=$(SERVER_LOCAL_POOLPATH) \
	-e PNS_LOGGER_LEVEL=$(LOGGER_LEVEL) \
	-e PNS_LOGGER_LEVEL_EXTRAS=$(LOGGER_LEVEL_EXTRAS) \
	-e PNS_BASEURL=$(BASEURL) \
	--name $$SN $(D) $(LATEST) $(LAU) ;\
	docker ps -n 1
	if [ $$? -gt 0 ]; then echo *** Launch failed; false; fi
	cid=`docker ps |grep $(LATEST) | head -n 1 |awk '{print $$1}'` ;\
	if [ -z $$cid ]; then echo NOT running ; false; fi ;\
	sleep 2;\
	echo docker inspect $$cid 

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

st_PIPCACHE=~/csc38/fdi/pipcache
st_WHEELS=~/csc38/fdi/wheels
PIPOPT=--disable-pip-version-check PROJ_PIPCACHE = $(st_PIPCACHE) PROJ_PIPWHEELS = $(st_WHEELS)
update_docker:
	(\
	$(MAKE) rm_docker &&\
	$(MAKE) docker_version &&\
	rm -f ../wheels/svom.product*.whl ;\
	$(MAKE) PROJ-INSTALL CLEAN=1 WHEEL_INSTALL=14 I="$(I)" $(PIPOPT) &&\
	$(MAKE) build_docker && $(MAKE) push_d PUSH_NAME=$(DOCKER_NAME) &&\
	$(MAKE) build_server && $(MAKE) push_d PUSH_NAME=$(SERVER_NAME) &&\
	$(MAKE) launch_test_server &&\
	$(MAKE) test_docker &&\
	$(MAKE) test_server &&\
	$(MAKE) rm_docker &&\
	@echo Done. `pwd; cat ./docker_version`) 2>&1 | tee update.log


cleanup:
	docker rmi -f `docker images -a|grep pool|awk 'BEGIN{FS=" "}{print $3}'`
	docker rmi -f `docker images -a|grep csc |awk 'BEGIN{FS=" "}{print $3}'`
	docker rmi -f `docker images -a|grep m/fdi|awk 'BEGIN{FS=" "}{print $3}'`

