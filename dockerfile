# syntax=docker/dockerfile:1.2

FROM ubuntu:18.04 AS fdi
# 1-6 M. Huang <mhuang@nao.cas.cn>
# 0.1 yuxin<syx1026@qq.com>
#ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHON_VER=3.8

User root

#ENV TZ=Etc/UTC
RUN apt-get update \
&& apt-get install -y apt-utils sudo nano net-tools locales graphviz  \
&& apt-get install -y git python3-pip python3.6-venv libpython3.6-dev \
python${PYTHON_VER}-venv python${PYTHON_VER} libpython${PYTHON_VER}-dev

# have to do this
RUN ln -s /usr/lib/x86_64-linux-gnu/libpython$libpython${PYTHON_VER}.so.1.0 /usr/lib/libpython$libpython${PYTHON_VER}.so.1.0 \
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
ARG UHOME=/home/${USR}
ARG PKG=fdi
WORKDIR ${UHOME}

# add user
RUN groupadd ${USR} && useradd -g ${USR} ${USR} -m --home=${UHOME} -G sudo -K UMASK=002\
&& /bin/echo -e '\n'${USR} ALL = NOPASSWD: ALL >> /etc/sudoers

# get passwords etc from ~/.secret
# update ~/.config/pnslocal.py so test can be run with correct settings
RUN --mount=type=secret,id=envs sudo cp /run/secrets/envs . \
&& sed -i -e 's/=/:=/' -e 's/^/s=${/' -e 's/$/}/' ./envs \
&& cat ./env \
&& sudo chown -R ${USR}:${USR} .

# Run as user
USER ${USR}

# If install fdi package
ENV PKGS_DIR=${UHOME}
RUN umask 0002

# copy fdi and .venv over
ADD --chown=${USR}:${USR} pipcache ${UHOME}/pipcache
ADD --chown=${USR}:${USR} wheels ${UHOME}/wheels
ADD --chown=${USR}:${USR} fdi ${UHOME}/fdi
# RUN pwd; echo --- \
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
RUN which python3; python3 --version; ls -l /usr/bin/py*
RUN python${PYTHON_VER} -m venv ${FDIVENV}

# effectively activate fdi virtual env for ${USR}
ENV PATH="${FDIVENV}/bin:$PATH"

# update pip
ARG PIPCACHE=${UHOME}/pipcache
ARG PIPWHEELS=${UHOME}/wheels
ARG PIPOPT="--cache-dir ${PIPCACHE} --no-index -f ${PIPWHEELS} --disable-pip-version-check"
RUN umask 0002 ; echo ${PIPOPT} \
&& python3 -m pip install ${PIPOPT} -U pip setuptools

RUN python3 -c 'import sys;print(sys.path)' \
&&  python3 -m pip list --format=columns \

&& which pip \
&& which python3
# ;cat .venv/bin/pip

WORKDIR ${UHOME}

# convenience aliases
COPY ./fdi/fdi/httppool/resources/profile .
RUN cat profile >> .bashrc && rm profile
### ADD .ssh ${UHOME}/.ssh

# config python.
#if venv is made with 'python3', python3 link needs to be made
# RUN ln -s /usr/bin/python3 ${FDIVENV}/bin/python3

# Configure permissions
#RUN for i in ${UHOME}/; do chown -R ${USR}:${USR} $i; echo $i; done 
#RUN chown ${USR}:${USR} ${PKGS_DIR}
### ADD .ssh ${UHOME}/.ssh
### RUN chmod 700 -R ${UHOME}/.ssh
### RUN ls -la ${UHOME}/.ssh

# install and test fdi
ARG fd=rebuild

WORKDIR ${PKGS_DIR}/${PKG}

# all dependents have to be from pip cache
RUN umask 0002 \
&& python3 -m pip install ${PIPOPT} --no-index -f ${PIPWHEELS} -e .[DEV,SERV,SCI]

WORKDIR ${PKGS_DIR}

# dockerfile_entrypoint.sh replaces IP/ports and configurations.
# GET THE LOCAL COPY, with possible uncommitted changes
RUN cp fdi/dockerfile_entrypoint.sh ./ \
&&  chmod 755 dockerfile_entrypoint.sh
# setup config files
RUN mkdir -p ${UHOME}/.config \
&& cp fdi/fdi/pns/config.py ${UHOME}/.config/pnslocal.py

# modify pnslocal.py
RUN cat ./envs \
&& ./dockerfile_entrypoint.sh  no-run  

WORKDIR ${PKGS_DIR}/${PKG}/
ARG TEST_OPTS=""
RUN pwd \
&& ls -ls \
&& envs \
&&  python3 -m pip list \
&& make -s -S test ${TEST_OPTS}
#\
#&& rm -rf /tmp/test* /tmp/data ${PIPCACHE} ${PIPWHEELS}

WORKDIR ${UHOME}

RUN pwd; /bin/ls -la; \
date > build

ENTRYPOINT  ["/home/fdi/dockerfile_entrypoint.sh"]
CMD ["/bin/bash"]

ARG DOCKER_VERSION
LABEL fdi ${DOCKER_VERSION}
ENV DOCKER_VERSION=${DOCKER_VERSION}
