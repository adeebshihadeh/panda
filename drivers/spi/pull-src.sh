#!/usr/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
cd $DIR

rm -f spidev.c
wget https://raw.githubusercontent.com/commaai/agnos-kernel-sdm845/master/drivers/spi/spidev.c

patch -o spidev_panda.c spidev.c -i patch
