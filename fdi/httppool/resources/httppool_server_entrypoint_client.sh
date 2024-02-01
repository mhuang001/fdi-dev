#!/bin/bash

id | tee ~/last_entrypoint.log
echo ###### update env using .env 

#set -a
#source ./envs
#echo rm ./envs

# if not set.
s=${UWSGIOPT:=''}
echo ###### if not set, logging level use WARNING in config
s=${PNS_LOGGER_LEVEL:=30}
set +a


sed -i "s/^conf\s*=\s*.*$/conf = 'production'/g" ~/.config/pnslocal.py 

date >> ~/last_entrypoint.log
cat ~/last_entrypoint.log
echo '>>>' $@

sleep 9e19
