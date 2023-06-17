#!/bin/bash
set -e

make

sudo rmmod pandaspi || true
sudo insmod pandaspi.ko

sudo lsmod
echo "loaded"
