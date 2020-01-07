#!/bin/sh
pyreverse -o png -p dataset+pal spdc/dataset spdc/pal
pyreverse -o png -p dataset spdc/dataset
pyreverse -o png -p pal spdc/pal
pyreverse -o png -p pns spdc/pns
