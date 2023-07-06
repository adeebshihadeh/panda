#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
cd $DIR

make -j8

sudo su -c "echo spi0.0 > /sys/bus/spi/drivers/spidev/unbind" || true

sudo dmesg -C

sudo rmmod pandaspi || true
sudo rmmod spidev_panda || true
#sudo insmod pandaspi.ko
sudo insmod spidev_panda.ko

sudo su -c "echo 'file $DIR/spidev_panda.c +p' > /sys/kernel/debug/dynamic_debug/control"

sudo lsmod

echo "loaded"
ls -la /dev/spi*
sudo chmod 666 /dev/spi*
ipython -c "from panda import Panda; print(Panda.list())"
dmesg
