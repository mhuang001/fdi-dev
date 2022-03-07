#!/bin/bash

id | tee ~/lastent
echo ######                                                                     

# if note set. use WARNING
s=${LOGGER_LEVEL:=30}

sed -i "s/^LOGGER_LEVEL =.*$/LOGGER_LEVEL = $LOGGER_LEVEL/g" ~/.config/pnslocal.py

sed -i "s/^EXTUSER =.*$/EXTUSER = \'$HOST_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTPASS =.*$/EXTPASS = \'$HOST_PASS\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTRO_USER =.*$/EXTRO_USER = \'$RO_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTRO_PASS =.*$/EXTRO_PASS = \'$RO_PASS\'/g" ~/.config/pnslocal.py

sed -i "s/^MQHOST =.*$/MQHOST = \'$MQ_HOST\'/g" ~/.config/pnslocal.py
sed -i "s/^MQPORT =.*$/MQPORT = $MQ_PORT/g" ~/.config/pnslocal.py
sed -i "s/^MQUSER =.*$/MQUSER = \'$MQ_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^MQPASS =.*$/MQPASS = \'$MQ_PASS\'/g" ~/.config/pnslocal.py


sed -i "s/^conf\s*=\s*.*$/conf = 'external'/g" ~/.config/pnslocal.py

echo =====  .config/pnslocal.py >> ~/lastent
grep ^conf  ~/.config/pnslocal.py >> ~/lastent

rm -rf /tmp/fditest* /tmp/data

date >> ~/lastent
cat ~/lastent

echo @@@ $@
for i in $@; do
if [ $i = no-run ]; then exit 0;else $@; fi;
done
