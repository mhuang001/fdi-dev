#!/bin/bash

id | tee ~/last_entrypoint.log
echo ###### update env using .env 

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
