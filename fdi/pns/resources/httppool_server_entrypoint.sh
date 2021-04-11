#!/bin/bash
IP=`ifconfig -a | grep "inet" | grep -v 127.0.0.1 | grep -v "inet6" | awk '{print $2}'`
HOST_IP=${SERVER_IP_ADDR}
HOST_PORT=${SERVER_PORT}
sed -i "s/<VirtualHost .*:.*$/<VirtualHost \*:$HOST_PORT>/g" /etc/apache2/sites-available/httppool_server.conf
sed -i "s/ServerName.*$/ServerName $IP/g" /etc/apache2/sites-available/httppool_server.conf
echo ===== /etc/apache2/sites-available/httppool_server.conf
grep Virtual /etc/apache2/sites-available/httppool_server.conf
grep ServerName /etc/apache2/sites-available/httppool_server.conf

sed -i "/^ServerName/d" -i "s/^#.*Global configuration.*$/&\n\nServerName $IP\n/" /etc/apache2/apache2.conf

echo ===== /etc/apache2/apache2.conf
grep -i ServerName /etc/apache2/apache2.conf

sed -i "s/^Listen .*/Listen ${HOST_PORT}/g" /etc/apache2/ports.conf
echo ===== /etc/apache2/ports.conf
grep Listen /etc/apache2/ports.conf

sed -i "s/^EXTHOST =.*$/EXTHOST = \'$IP\'/g" .config/pnslocal.py
sed -i "s/^EXTPORT =.*$/EXTPORT = $HOST_PORT/g" .config/pnslocal.py
sed -i "s/^conf\s*=\s*.*$/conf = 'external'/g" .config/pnslocal.py

echo =====  .config/pnslocal.py
grep ^conf  .config/pnslocal.py
grep ^EXTHOST  .config/pnslocal.py
grep ^EXTPORT  .config/pnslocal.py
