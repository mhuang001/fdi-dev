#!/bin/bash

id | tee ~/lastent
echo ######

set -a
source ./envs
echo rm ./envs
set +a

sed -i "s/^LOGGER_LEVEL =.*$/LOGGER_LEVEL = $LOGGER_LEVEL/g" ~/.config/pnslocal.py

sed -i "s/^EXTHOST =.*$/EXTHOST = \'$HOST_IP\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTPORT =.*$/EXTPORT = $HOST_PORT/g" ~/.config/pnslocal.py
sed -i "s/^EXTUSER =.*$/EXTUSER = \'$HOST_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTPASS =.*$/EXTPASS = \'$HOST_PASS\'/g" ~/.config/pnslocal.py
sed -i "s/^SELF_HOST =.*$/SELF_HOST = \'$SELF_HOST\'/g" ~/.config/pnslocal.py
sed -i "s/^SELF_PORT =.*$/SELF_PORT = $SELF_PORT/g" ~/.config/pnslocal.py
sed -i "s/^EXTRO_USER =.*$/EXTRO_USER = \'$RO_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTRO_PASS =.*$/EXTRO_PASS = \'$RO_PASS\'/g" ~/.config/pnslocal.py

sed -i "s/^MQHOST =.*$/MQHOST = \'$MQ_HOST\'/g" ~/.config/pnslocal.py
sed -i "s/^MQPORT =.*$/MQPORT = $MQ_PORT/g" ~/.config/pnslocal.py
sed -i "s/^MQUSER =.*$/MQUSER = \'$MQ_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^MQPASS =.*$/MQPASS = \'$MQ_PASS\'/g" ~/.config/pnslocal.py


sed -i "s/^conf\s*=\s*.*$/conf = 'external'/g" ~/.config/pnslocal.py

echo =====  .config/pnslocal.py >> ~/lastent
grep ^conf  ~/.config/pnslocal.py >> ~/lastent
grep ^EXTHOST  ~/.config/pnslocal.py >> ~/lastent
grep ^EXTPORT  ~/.config/pnslocal.py >> ~/lastent
grep ^EXTUSER  ~/.config/pnslocal.py >> ~/lastent
grep ^SELF_HOST  ~/.config/pnslocal.py >> ~/lastent
grep ^SELF_PORT  ~/.config/pnslocal.py >> ~/lastent
grep ^SELF_USER  ~/.config/pnslocal.py >> ~/lastent
grep ^API_BASE  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^BASE_POOLPATH  ~/.config/pnslocal.py >> ~/lastent
grep ^SERVER_POOLPATH  ~/.config/pnslocal.py >> ~/lastent
grep ^LOGGER_LEVEL  ~/.config/pnslocal.py >> ~/lastent

rm -rf /tmp/fditest* /tmp/data

date >> ~/lastent
cat ~/lastent

echo @@@ $@
for i in $@; do
if [ $i = no-run ]; then exit 0; fi;
done

exec "$@"
