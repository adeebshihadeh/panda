#!/bin/bash
set -e

make

sudo su -c "echo spi0.0 > /sys/bus/spi/drivers/spidev/unbind" || true

sudo rmmod pandaspi || true
sudo insmod pandaspi.ko

sudo lsmod
echo "loaded"
