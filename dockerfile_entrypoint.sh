#!/bin/bash

id | tee ~/lastent
echo ######

set -a
source ./envs
echo do not rm ./envs
set +a


rm -rf /tmp/fditest* /tmp/data

date >> ~/lastent
cat ~/lastent

echo @@@ $@
for i in $@; do
if [ $i = no-run ]; then exit 0; fi;
done

exec "$@"
