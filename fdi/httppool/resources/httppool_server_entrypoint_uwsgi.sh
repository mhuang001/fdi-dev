#!/bin/bash

id | tee ~/last_entry.log
echo ######                                                                     
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
sed -i "s/^LOGGING_LEVEL =.*$/LOGGING_LEVEL = $LOGGING_LEVEL/g" ~/.config/pnslocal.py

sed -i "s/^conf\s*=\s*.*$/conf = 'external'/g" ~/.config/pnslocal.py 

echo =====  .config/pnslocal.py >> ~/last_entry.log
grep ^conf  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^EXTHOST  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^EXTPORT  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^SELF_HOST  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^SELF_PORT  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^BASE_POOLPATH  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^SERVER_POOLPATH  ~/.config/pnslocal.py >> ~/last_entry.log

date >> ~/last_entry.log
cat ~/last_entry.log
echo @@@ $@
for i in $@; do
if [ $i = no-run ]; then exit 0;else $@; fi;
done

