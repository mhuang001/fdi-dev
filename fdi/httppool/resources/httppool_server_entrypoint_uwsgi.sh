#!/bin/bash

id | tee ~/last_entrypoint.log
echo ###### update env using .env 

#set -a
#source ./envs
#echo rm ./envs

# if not set.
s=${UWSGIOPT:=''}
echo ###### if not set, logging level use WARNING in config
s=${PNS_LOGGER_LEVEL:=30}
set +a

sed -i "s/^conf\s*=\s*.*$/conf = 'production'/g" ~/.config/pnslocal.py 
mkdir -p /var/log/uwsgi

if [ ! -d /var/log/uwsgi ]; then \
sudo mkdir -p /var/log/uwsgi && \
sudo chown -R fdi:fdi /var/log/uwsgi && \
chmod 755 /var/log/uwsgi ; fi

mkdir -p ${PNS_SERVER_LOCAL_POOLPATH}
if [ ! -O ${PNS_SERVER_LOCAL_POOLPATH} ]; then \
sudo chown -R fdi:fdi  ${PNS_SERVER_LOCAL_POOLPATH}; fi

#ls -l /var/log ${PNS_SERVER_LOCAL_POOLPATH} >> ~/last_entrypoint.log
				 
date >> ~/last_entrypoint.log
cat ~/last_entrypoint.log
echo '>>>' $@
for i in $@; do
if [ $i = no-run ]; then exit 0; fi;
done

exec "$@"
