# syntax=docker/dockerfile:1.2

FROM ubuntu:18.04 AS fdi
LABEL fdi 1.6
# 1-1.3 M. Huang <mhuang@nao.cas.cn>
# 0.1 yuxin<syx1026@qq.com>
#ARG DEBIAN_FRONTEND=noninteractive
#ENV TZ=Etc/UTC
RUN apt-get update \
&& apt-get install -y apt-utils sudo nano net-tools\
&& apt-get install -y git python3-pip python3-venv
#&& rm -rf /var/lib/apt/lists/*

# rebuild mark
ARG re=rebuild

# setup env
# setup user
ARG USR=fdi
ARG UHOME=/home/${USR}

RUN groupadd ${USR} && useradd -g ${USR} ${USR} -m --home=${UHOME} -G sudo -K UMASK=002\
&& mkdir -p ${UHOME}/.config \
&& /bin/echo -e '\n'${USR} ALL = NOPASSWD: ALL >> /etc/sudoers

WORKDIR ${UHOME}

USER ${USR}
ENV PATH="${UHOME}/.local/bin:$PATH"

# set fdi's virtual env
# let group access cache and bin. https://stackoverflow.com/a/46900270
ENV FDIVENV=${UHOME}/.venv
RUN umask 0002 && python3.6 -m venv ${FDIVENV}

# effectively activate fdi virtual env for ${USR}
ENV PATH="${FDIVENV}/bin:$PATH"

# this also upgrades pip
#RUN pip3 install pipenv
RUN umask 0002 \
&& python3 -m pip install pip -U

# convenience aliases
COPY fdi/pns/resources/profile .
RUN cat profile >> .bashrc && rm profile


USER root
# config python.
#if venv is made with 'python3', python3.6 link needs to be made
# RUN ln -s /usr/bin/python3.6 ${FDIVENV}/bin/python3.6

# Configure permission
RUN for i in /var/run/lock/ ${UHOME}/; \
do chown -R ${USR}:${USR} $i; echo $i; done 

# If install fdi repo, instead of package
# make dir for fdi.
ENV PKGS_DIR=${UHOME}
RUN mkdir -p ${PKGS_DIR} && chown ${USR}:${USR} ${PKGS_DIR}

# Run as user
USER ${USR}

# install and test fdi
ARG fd=rebuild

WORKDIR ${PKGS_DIR}
ARG PKG=fdi
# from local repo. UNCOMMITED CHANGES ARE NOT INCUDED.
COPY --chown=${USR}:${USR} ./ /tmp/fdi_repo/
RUN git clone --depth 20 -b develop  file:///tmp/fdi_repo ${PKG}
WORKDIR ${PKGS_DIR}/${PKG}/

#ENV FDIVENV ${PKGS_DIR}/${PKG}/.venv
ENV PIPENV_VENV_IN_PROJECT 1

# let group access cache and bin. https://stackoverflow.com/a/46900270
RUN umask 0002 \
&& python3.6 -m pip install -e .[DEV,SERV] \
&& python3.6 -c 'import sys;print(sys.path)' &&  pip list

WORKDIR ${PKGS_DIR}

# dockerfile_entrypoint.sh replaces IP/ports and configurations.
# GET THE LOCAL COPY, with possible uncommited chhanges
COPY --chown=${USR}:${USR} dockerfile_entrypoint.sh ./
RUN  chmod 755 dockerfile_entrypoint.sh
# setup config files
COPY --chown=${USR}:${USR} fdi/pns/config.py ${UHOME}/.config/pnslocal.py

USER ${USR}
# get passwords etc from ~/.secret
RUN --mount=type=secret,id=envs sudo cp /run/secrets/envs . \
&& sudo chown ${USR} envs \
&& /bin/bash -c 'for i in `cat ./envs`; do export $i; done \
&& ./dockerfile_entrypoint.sh  no-run'  # modify pnslocal.py
#RUN bash -c 'for i in `sed -e 's/=.*$//g' ./envs`; do echo $i=${!i}, PPP ${GITPULLCSC} P%%%; done'

WORKDIR ${PKGS_DIR}/${PKG}/
RUN make test \
&& rm -rf /tmp/fdi_repo

WORKDIR ${UHOME}

RUN pwd; /bin/ls -la; \
date > build

ENTRYPOINT  ["/home/fdi/dockerfile_entrypoint.sh"]

