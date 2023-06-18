#!/bin/bash
set -e

make -j8

sudo su -c "echo spi0.0 > /sys/bus/spi/drivers/spidev/unbind" || true

sudo rmmod pandaspi || true
sudo rmmod spidev_panda || true
#sudo insmod pandaspi.ko
sudo insmod spidev_panda.ko

sudo lsmod
echo "loaded"
