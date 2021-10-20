#!/bin/bash

id | tee ~/last_entry.log
echo ######                                                                     
IP=`ifconfig -a | grep "inet" | grep -v 127.0.0.1 | grep -v "inet6" | awk '{print $2}'`
#HOST_PORT=${SERVER_PORT}
sudo sed -i "s/<VirtualHost .*:.*$/<VirtualHost \*:$HOST_PORT>/g" /etc/apache2/sites-available/httppool_server.conf
sudo sed -i "s/ServerName.*$/ServerName $IP/g" /etc/apache2/sites-available/httppool_server.conf
echo ===== /etc/apache2/sites-available/httppool_server.conf >> ~/last_entry.log
grep Virtual /etc/apache2/sites-available/httppool_server.conf >> ~/last_entry.log
grep ServerName /etc/apache2/sites-available/httppool_server.conf >> ~/last_entry.log

sudo sed -i "/^ServerName/d" /etc/apache2/apache2.conf
sudo sed -i "s/^#.*Global configuration.*$/&\n\nServerName $IP\n/" /etc/apache2/apache2.conf

echo ===== /etc/apache2/apache2.conf >> ~/last_entry.log
grep -i ServerName /etc/apache2/apache2.conf >> ~/last_entry.log

sudo sed -i "s/^Listen .*/Listen ${HOST_PORT}/g" /etc/apache2/ports.conf
echo ===== /etc/apache2/ports.conf >> ~/last_entry.log
grep Listen /etc/apache2/ports.conf >> ~/last_entry.log


sed -i "s/^EXTHOST =.*$/EXTHOST = \'$IP\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTPORT =.*$/EXTPORT = $HOST_PORT/g" ~/.config/pnslocal.py
sed -i "s/^EXTUSER =.*$/EXTUSER = \'$HOST_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTPASS =.*$/EXTPASS = \'$HOST_PASS\'/g" ~/.config/pnslocal.py

sed -i "s/^MQHOST =.*$/MQHOST = \'$MQ_HOST\'/g" ~/.config/pnslocal.py
sed -i "s/^MQPORT =.*$/MQPORT = $MQ_PORT/g" ~/.config/pnslocal.py
sed -i "s/^MQUSER =.*$/MQUSER = \'$MQ_USER\'/g" ~/.config/pnslocal.py
sed -i "s/^MQPASS =.*$/MQPASS = \'$MQ_PASS\'/g" ~/.config/pnslocal.py

sed -i "s|^API_BASE =.*$|API_BASE = \'$API_BASE\'|g" ~/.config/pnslocal.py
sed -i "s|^SERVER_POOLPATH =.*$|SERVER_POOLPATH = \'$SERVER_POOLPATH\'|g" ~/.config/pnslocal.py
sed -i "s/^LOGGING_LEVEL =.*$/LOGGING_LEVEL = $LOGGING_LEVEL/g" ~/.config/pnslocal.py

sed -i "s/^conf\s*=\s*.*$/conf = 'external'/g" ~/.config/pnslocal.py 

echo =====  .config/pnslocal.py >> ~/last_entry.log
grep ^conf  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^EXTHOST  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^EXTPORT  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^BASE_POOLPATH  ~/.config/pnslocal.py >> ~/last_entry.log
grep ^SERVER_POOLPATH  ~/.config/pnslocal.py >> ~/last_entry.log

date >> ~/last_entry.log
cat ~/last_entry.log
echo @@@ $@
for i in $@; do
if [ $i = no-run ]; then exit 0; fi;
done

echo enabling site ... >> ~/last_entry.log
sudo a2ensite httppool_server.conf
sudo a2dissite 000-default.conf
service apache2 reload && echo apache2 reloaded;
echo running apachectl in CMD...>> ~/last_entry.log  ;
/usr/sbin/apache2ctl -DFOREGROUND 2>&1 >> ~/last_entry.log
