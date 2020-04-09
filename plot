#!/bin/sh
pyreverse -o png -p dataset+pal fdi/dataset fdi/pal
pyreverse -o png -p dataset fdi/dataset
pyreverse -o png -p pal fdi/pal
pyreverse -o png -p pns fdi/pns
