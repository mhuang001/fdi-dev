# syntax=docker/dockerfile:1.2

FROM ubuntu:18.04 AS fdi
LABEL fd1 1.6
# 0.2-4 M. Huang <mhuang@nao.cas.cn>
# 0.1 yuxin<syx1026@qq.com>
#ARG DEBIAN_FRONTEND=noninteractive
#ENV TZ=Etc/UTC
RUN apt-get update \
&& apt-get install -y apt-utils sudo nano net-tools\
&& apt-get install -y git python3-pip

# rebuild mark
ARG re=rebuild

# setup env

# setup user
ARG USR=fdi
ARG UHOME=/home/${USR}
RUN groupadd ${USR} && useradd -g ${USR} ${USR} -m --home=${UHOME} -G sudo \
&& mkdir -p ${UHOME}/.config \
&& /bin/echo -e '\n'${USR} ALL = NOPASSWD: ALL >> /etc/sudoers

WORKDIR ${UHOME}
ENV PATH="${UHOME}/.local/bin:$PATH"

# config software
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.6 0 \
&& python3 -m pip install pip -U

# convinience aliases
COPY fdi/pns/resources/profile .
RUN cat profile >> .bashrc && rm profile

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
RUN make install EXT="[DEV,SERV]" I="--user"

# If installing fdi package
# no [DEV] needed
#RUN python3 -m pip install http://mercury.bao.ac.cn:9006/mh/fdi/-/archive/develop/fdi-develop.tar.gz#egg=fdi[DEV,SERV]
#RUN python3 -m pip install fdi[DEV,SERV]

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
&& for i in `cat ./envs`; do export $i; done \
&& ./dockerfile_entrypoint.sh  no-run  # modify pnslocal.py

WORKDIR ${PKGS_DIR}/${PKG}/
RUN make test \
&& rm -rf /tmp/fdi_repo

WORKDIR ${UHOME}

RUN pwd; /bin/ls -la; \
date > build

ENTRYPOINT  ["/home/fdi/dockerfile_entrypoint.sh"]