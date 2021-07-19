#!/bin/bash

id | tee ~/lastent
echo ######                                                                     

IP=`ifconfig -a | grep "inet" | grep -v 127.0.0.1 | grep -v "inet6" | awk '{print $2}'`

sed -i "s/^EXTHOST =.*$/EXTHOST = \'$IP\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTPORT =.*$/EXTPORT = $HOST_PORT/g" ~/.config/pnslocal.py
sed -i "s/^EXTUSER =.*$/EXTUSER = \'$HOST_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTPASS =.*$/EXTPASS = \'$HOST_PASS\'/g" ~/.config/pnslocal.py

sed -i "s/^MQHOST =.*$/MQHOST = \'$MQ_HOST\'/g" ~/.config/pnslocal.py
sed -i "s/^MQPORT =.*$/MQPORT = $MQ_PORT/g" ~/.config/pnslocal.py
sed -i "s/^MQUSER =.*$/MQUSER = \'$MQ_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^MQPASS =.*$/MQPASS = \'$MQ_PASS\'/g" ~/.config/pnslocal.py


sed -i "s/^conf\s*=\s*.*$/conf = 'external'/g" ~/.config/pnslocal.py

echo =====  .config/pnslocal.py >> ~/lastent
grep ^conf  ~/.config/pnslocal.py >> ~/lastent
grep ^EXTHOST  ~/.config/pnslocal.py >> ~/lastent
grep ^EXTPORT  ~/.config/pnslocal.py >> ~/lastent
grep ^BASE_POOLPATH  ~/.config/pnslocal.py >> ~/lastent
grep ^SERVER_POOLPATH  ~/.config/pnslocal.py >> ~/lastent


date >> ~/lastent
cat ~/lastent

echo @@@ $@
for i in $@; do
if [ $i = no-run ]; then exit 0; fi;
done

/bin/sleep 99999999999

