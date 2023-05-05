DOCKER_NAME	= fdi
DFILE	=fdi/dockerfile

SERVER_NAME      =httppool
BASEURL = $(shell python -m fdi.utils.getconfig baseurl)

API_VERSION	= $(shell python -m fdi.utils.getconfig api_version)
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

include  Makefile_docker_common.mk
