#!/usr/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
cd $DIR

wget https://raw.githubusercontent.com/commaai/agnos-kernel-sdm845/master/drivers/spi/spidev.c

cp spidev.c spidev_panda.c

