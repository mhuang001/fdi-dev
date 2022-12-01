#!/bin/bash

id | tee ~/lastent_docker
echo ######

rm -rf /tmp/fditest* /tmp/data

date >> ~/lastent_docker
cat ~/lastent_docker

echo @@@ $@
for i in $@; do
if [ $i = no-run ]; then exit 0; fi;
done

exec "$@"
