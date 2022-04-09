#!/bin/bash

id | tee ~/last_entry.log
echo ######

set -a
source ./envs
echo rm ./envs

# if note set.
s=${UWSGIOPT:=''}
set +a

sed -i "s/^EXTHOST =.*$/EXTHOST = \'$HOST_IP\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTPORT =.*$/EXTPORT = $HOST_PORT/g" ~/.config/pnslocal.py
sed -i "s/^EXTUSER =.*$/EXTUSER = \'$HOST_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTPASS =.*$/EXTPASS = \'$HOST_PASS\'/g" ~/.config/pnslocal.py

sed -i "s/^MQHOST =.*$/MQHOST = \'$MQ_HOST\'/g" ~/.config/pnslocal.py
sed -i "s/^MQPORT =.*$/MQPORT = $MQ_PORT/g" ~/.config/pnslocal.py
sed -i "s/^MQUSER =.*$/MQUSER = \'$MQ_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^MQPASS =.*$/MQPASS = \'$MQ_PASS\'/g" ~/.config/pnslocal.py

sed -i "s/^SELF_HOST =.*$/SELF_HOST = \'$SELF_HOST\'/g" ~/.config/pnslocal.py
sed -i "s/^SELF_PORT =.*$/SELF_PORT = $SELF_PORT/g" ~/.config/pnslocal.py
sed -i "s/^SELF_USER =.*$/SELF_USER = \'$SELF_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^SELF_PASS =.*$/SELF_PASS = \'$SELF_PASS\'/g" ~/.config/pnslocal.py

sed -i "s|^API_BASE =.*$|API_BASE = \'$API_BASE\'|g" ~/.config/pnslocal.py
sed -i "s|^SERVER_POOLPATH =.*$|SERVER_POOLPATH = \'$SERVER_POOLPATH\'|g" ~/.config/pnslocal.py
# if note set. use WARNING
s=${LOGGER_LEVEL:=30}
sed -i "s/^LOGGER_LEVEL =.*$/LOGGER_LEVEL = $LOGGER_LEVEL/g" ~/.config/pnslocal.py

sed -i "s/^conf\s*=\s*.*$/conf = 'external'/g" ~/.config/pnslocal.py 
mkdir -p /var/log/uwsgi

echo =====  .config/pnslocal.py >> ~/last_entry.log
grep ^conf  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^EXTHOST  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^EXTPORT  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^EXTUSER  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^SELF_HOST  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^SELF_PORT  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^SELF_USER  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^API_BASE  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^SERVER_POOLPATH  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^LOGGER_LEVEL  ~/.config/pnslocal.py >> ~/last_entry.log

if [ ! -d /var/log/uwsgi ]; then \
sudo mkdir -p /var/log/uwsgi && \
sudo chown -R fdi /var/log/uwsgi && \
sudo chgrp -R fdi /var/log/uwsgi && \
chmod 755 /var/log/uwsgi ; fi

mkdir -p /var/www/httppool_server/data
if [ ! -O /var/www/httppool_server/data ]; then \
sudo chown -R fdi:fdi  /var/www/httppool_server/data; fi

#ls -l /var/log /var/www/httppool_server/data >> ~/last_entry.log
				 
date >> ~/last_entry.log
cat ~/last_entry.log
echo '>>>' $@
for i in $@; do
if [ $i = no-run ]; then exit 0; fi;
done

exec "$@"
