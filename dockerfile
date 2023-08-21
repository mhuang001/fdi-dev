# syntax=docker/dockerfile:1.2

FROM ubuntu:18.04 AS fdi
# 8 inherit ENTRYPOINT
# 1-6 M. Huang <mhuang@nao.cas.cn>
# 0.1 yuxin<syx1026@qq.com>
#ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHON_VER=3.8
ARG PYEXE=python${PYTHON_VER}
ENV PYEXE=${PYEXE}

User root

#ENV TZ=Etc/UTC
RUN apt-get update \
&& apt-get install -y apt-utils sudo nano net-tools telnet locales graphviz  \
&& apt-get install -y git python3-pip python3.6-venv libpython3.6-dev \
${PYEXE}-venv ${PYEXE} lib${PYEXE}-dev

# have to do this
RUN ln -s /usr/lib/x86_64-linux-gnu/libpython$lib${PYEXE}.so.1.0 /usr/lib/libpython$lib${PYEXE}.so.1.0 \
&& rm -rf /var/lib/apt/lists/*

# rebuild mark
ARG re=rebuild
RUN echo ${re} > /tmp/rebuild_mark

# setup env

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/'  /etc/locale.gen \
&& locale-gen \
&& dpkg-reconfigure --frontend=noninteractive locales


# setup user
ARG USR=fdi
ENV USR=${USR}
ARG UHOME=/home/${USR}
ENV UHOME=${UHOME}
ENV PKGS_DIR=/home/${USR}

ARG PKG=fdi

ARG LOGGER_LEVEL=30
ENV PNS_LOGGER_LEVEL=${LOGGER_LEVEL}

WORKDIR ${UHOME}

# add user
RUN groupadd ${USR} && useradd -g ${USR} ${USR} -m --home=${UHOME} -G sudo -K UMASK=002\
&& /bin/echo -e '\n'${USR} ALL = NOPASSWD: ALL >> /etc/sudoers

RUN mkdir -p -m 0700 ${UHOME}/.ssh
RUN --mount=type=secret,id=sshpri sudo cp /run/secrets/sshpri ${UHOME}/.ssh/id_rsa
RUN --mount=type=secret,id=sshpub sudo cp /run/secrets/sshpub ${UHOME}/.ssh/id_rsa.pub
RUN sudo chown -R ${USR}:${USR} ${UHOME}/.ssh
RUN cp ${UHOME}/.ssh/id_rsa.pub ${UHOME}/.ssh/authorized_keys \
&& chmod 0600 ${UHOME}/.ssh/* \
&& ls -l ${UHOME}/.ssh

#&& echo xxx cat ${UHOME}/.ssh/id_rsa

# get passwords etc from ~/.secret with old method
# RUN --mount=type=secret,id=envs sudo cp /run/secrets/envs . 

RUN umask 0002 ; pwd; echo ${PIPOPT} ----\
&& python3 -m pip install -U pip setuptools

RUN sudo chown -R ${USR}:${USR} .

# Run as user
USER ${USR}

RUN umask 0002

# copy fdi and .venv over
ARG PIPCACHE=${UHOME}/pipcache
ENV PIPCACHE=${UHOME}/pipcache
ARG PIPWHEELS=${UHOME}/wheels
ENV PIPWHEELS=${UHOME}/wheels
ADD --chown=${USR}:${USR} pipcache ${PIPCACHE}
ADD --chown=${USR}:${USR} wheels ${PIPWHEELS}
ADD --chown=${USR}:${USR} fdi ${UHOME}/fdi
RUN pwd; echo --- ; du -sh *
# && ls wheels ; echo --- \
# && ls . ; echo --- \
# && ls ${PKG}

ARG LOCALE=en_US.UTF-8
ENV LC_ALL=${LOCALE}
ENV LC_CTYPE=${LOCALE}
ENV LANG=${LOCALE}

ARG LOGGER_LEVEL=10
ENV PNS_LOGGER_LEVEL=${LOGGER_LEVEL}
ARG LOGGER_LEVEL_EXTRAS=30
ENV PNS_LOGGER_LEVEL_EXTRAS=${LOGGER_LEVEL_EXTRAS}

# set fdi's virtual env
# let group access cache and bin. https://stackoverflow.com/a/46900270
ENV FDIVENV=${UHOME}/.venv
RUN which python3; python3 --version #; ls -l /usr/bin/py*
RUN ${PYEXE} -m venv ${FDIVENV}

# effectively activate fdi virtual env for ${USR}
ENV PATH="${FDIVENV}/bin:$PATH"

# use copied cache and wheels
ARG PIPOPT="--cache-dir ${PIPCACHE} -f ${PIPWHEELS} --disable-pip-version-check"

# update pip
WORKDIR ${UHOME}
RUN umask 0002 \
&& ${PYEXE} -m pip install pip setuptools ${PIPOPT} -U 

RUN ${PYEXE} -c 'import sys;print(sys.path)' \
&&  ${PYEXE} -m pip list --format=columns \
&& which pip \
&& which python3
# ;cat .venv/bin/pip

# convenience aliases
COPY ./fdi/fdi/httppool/resources/profile .
RUN cat profile >> .bashrc && rm profile

# config python.
#if venv is made with 'python3', ${PYEXE} link needs to be made
# RUN ln -s /usr/bin/${PYEXE} ${FDIVENV}/bin/python3

# Configure permissions
#RUN for i in ${UHOME}/; do chown -R ${USR}:${USR} $i; echo $i; done 
#RUN chown ${USR}:${USR} ${PKGS_DIR}

# install fdi
ARG fd=rebuild

WORKDIR ${PKGS_DIR}/${PKG}

# all dependents have to be from pip cache
RUN umask 0002 \
&& make PROJ-INSTALL WHEEL_INSTALL=14 fdi_EXT="[DEV,SCI]" I="-q"
#&& ${PYEXE} -m pip install -e .[DEV,SCI] ${PIPOPT}

WORKDIR ${PKGS_DIR}

# GET THE LOCAL COPY, with possible uncommitted changes
RUN cp fdi/dockerfile_entrypoint.sh ./ \
&&  chmod 755 dockerfile_entrypoint.sh
# setup config files
RUN mkdir -p ${UHOME}/.config \
&& cp fdi/fdi/pns/config.py ${UHOME}/.config/pnslocal.py


RUN rm -rf /tmp/test* /tmp/data

WORKDIR ${UHOME}

RUN pwd; /bin/ls -la; env \
date > build

# https://dev.to/francescobianco/override-docker-entrypoint-sh-into-dockerfile-4fh

# USER root
COPY /home/fdi/fdi/dockerfile_entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN echo /bin/bash > /usr/local/bin/service-foreground.sh
RUN chown ${USR}:${USR} /usr/local/bin/service-foreground.sh /usr/local/bin/docker-entrypoint.sh

# USER ${USR}
# RUN chmod +x  /usr/local/bin/service-foreground.sh /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["service-foreground.sh"]

ARG DOCKER_VERSION
ENV PNS_DOCKER_VERSION=${DOCKER_VERSION}
LABEL fdi ${PNS_DOCKER_VERSION}
