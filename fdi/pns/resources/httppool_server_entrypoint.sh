#!/bin/bash
IP=`ifconfig -a | grep "inet" | grep -v 127.0.0.1 | grep -v "inet6" | awk '{print $2}'`
HOST_IP=${SERVER_IP_ADDR}
HOST_PORT=${SERVER_PORT}
sed -i "s/{SERVER_IP_ADDR}/$IP/g" /etc/apache2/sites-available/httppool_server.conf
sed -i "s/{SERVER_PORT}/${HOST_PORT}/g" /etc/apache2/sites-available/httppool_server.conf
echo ===== /etc/apache2/sites-available/httppool_server.conf
grep Virtual /etc/apache2/sites-available/httppool_server.conf
grep ServerName /etc/apache2/sites-available/httppool_server.conf

sed -i "s/^Listen .*/Listen ${HOST_PORT}/g" /etc/apache2/ports.conf
echo ===== /etc/apache2/ports.conf
grep Listen /etc/apache2/ports.conf

# cat << EOC >>  .config/pnslocal.py
# auto-generated by entrypoint.sh to override above. DO not edit
# EOC
#echo =====  .config/pnslocal.py
#tail -8 .config/pnslocal.py
