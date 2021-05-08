#!/bin/bash
id | tee ~/lastent
echo ######                                                                     

IP=`ifconfig -a | grep "inet" | grep -v 127.0.0.1 | grep -v "inet6" | awk '{print $2}'`
#HOST_IP=${SERVER_IP_ADDR}
HOST_PORT=${SERVER_PORT}
sudo sed -i "s/<VirtualHost .*:.*$/<VirtualHost \*:$HOST_PORT>/g" /etc/apache2/sites-available/httppool_server.conf
sudo sed -i "s/ServerName.*$/ServerName $IP/g" /etc/apache2/sites-available/httppool_server.conf
echo ===== /etc/apache2/sites-available/httppool_server.conf >> ~/lastent
grep Virtual /etc/apache2/sites-available/httppool_server.conf >> ~/lastent
grep ServerName /etc/apache2/sites-available/httppool_server.conf >> ~/lastent

sudo sed -i "/^ServerName/d" /etc/apache2/apache2.conf
sudo sed -i "s/^#.*Global configuration.*$/&\n\nServerName $IP\n/" /etc/apache2/apache2.conf

echo ===== /etc/apache2/apache2.conf >> ~/lastent
grep -i ServerName /etc/apache2/apache2.conf >> ~/lastent

sudo sed -i "s/^Listen .*/Listen ${HOST_PORT}/g" /etc/apache2/ports.conf
echo ===== /etc/apache2/ports.conf >> ~/lastent
grep Listen /etc/apache2/ports.conf >> ~/lastent

sudo a2ensite httppool_server.conf
sudo a2dissite 000-default.conf


sed -i "s/^EXTHOST =.*$/EXTHOST = \'$IP\'/g" ~/.config/pnslocal.py
sed -i "s/^EXTPORT =.*$/EXTPORT = $HOST_PORT/g" ~/.config/pnslocal.py
sed -i "s/^conf\s*=\s*.*$/conf = 'external'/g" ~/.config/pnslocal.py

echo =====  .config/pnslocal.py >> ~/lastent
grep ^conf  ~/.config/pnslocal.py >> ~/lastent
grep ^EXTHOST  ~/.config/pnslocal.py >> ~/lastent
grep ^EXTPORT  ~/.config/pnslocal.py >> ~/lastent

#service apache2 reload && echo apache2 reloaded

date >> ~/lastent

echo running apachectl >> ~/lastent
exec /usr/sbin/apache2ctl -DFOREGROUND 2>&1 >> ~/lastent

