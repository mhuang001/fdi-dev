#!/bin/bash


date >> ~/last_ent_fdi
cat ~/lastent_docker

echo @@@ $@
for i in $@; do
if [ $i = no-run ]; then exit 0; fi;
done

exec "$@"
