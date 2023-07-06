#include <linux/delay.h>
#include <linux/spi/spi.h>
#include <linux/spi/spidev.h>

#define SPI_SYNC 0x5AU
#define SPI_HACK 0x79U
#define SPI_DACK 0x85U
#define SPI_NACK 0x1FU
#define SPI_BUF_SIZE 1024
#define SPI_CHECKSUM_START 0xABU

enum SpiError {
  NACK = -2,
  ACK_TIMEOUT = -3,
};

struct __attribute__((packed)) spi_header {
  u8 sync;
  u8 endpoint;
  uint16_t tx_len;
  uint16_t max_rx_len;
};

struct spi_panda_transfer {
  __u64 rx_buf;
  __u64 tx_buf;
  __u32 tx_length;
  __u32 rx_length_max;
  __u32 timeout;
  __u8 endpoint;
  __u8 expect_disconnect;
};

static void
panda_set_checksum(__u8 *buf, __u16 length) {
  int i;
  __u8 checksum = 0xab;
  for (i = 0; i < length; i++) {
    checksum ^= buf[i];
  } 
  buf[length] = checksum;
}

static __u8
panda_check_checksum(__u8 *buf, __u16 length) {
  int i;
  __u8 checksum = SPI_CHECKSUM_START;
  for (i = 0U; i < length; i++) {
    checksum ^= buf[i];
  }
  return checksum == 0U;
}

static long
panda_wait_for_ack(struct spidev_data *spidev, __u8 ack_val) {
  int i;
  int ret;
  for (i = 0; i < 1000; i++) {
    ret = spidev_sync_read(spidev, 1);
    if (ret < 0) {
      continue;
      //return ret;
    }
    if (spidev->rx_buffer[0] == ack_val) {
      return 0;
    }
    usleep_range(100, 500);
  }
  return -1;
}


static long
panda_transfer(struct spidev_data *spidev, struct spi_device *spi, unsigned long arg) {
  long retval = -1;

  // read struct from user
  struct spi_panda_transfer pt;
  if (!access_ok(VERIFY_WRITE, arg, sizeof(pt))) {
    retval = -EFAULT;
    goto end;
  }
  if (copy_from_user(&pt, (void __user *)arg, sizeof(pt))) {
    retval = -EFAULT;
    goto end;
  }
  dev_dbg(&spi->dev, "ep: %d, tx len: %d\n", pt.endpoint, pt.tx_length);

  // send header
  struct spi_header sh = {
    .sync = 0x5a,
    .endpoint = pt.endpoint,
    .tx_len = pt.tx_length,
    .max_rx_len = pt.rx_length_max
  };
  memcpy(spidev->tx_buffer, &sh, sizeof(sh));
  panda_set_checksum(spidev->tx_buffer, sizeof(sh));
  retval = spidev_sync_write(spidev, sizeof(sh) + 1);

  // wait for ACK
  retval = panda_wait_for_ack(spidev, SPI_HACK);
  if (retval < 0) {
    dev_dbg(&spi->dev, "no header ack\n");
    goto end;
  }

  // send data
  dev_dbg(&spi->dev, "sending data\n");
  retval = copy_from_user(spidev->tx_buffer, (const u8 __user *)(uintptr_t)pt.tx_buf, pt.tx_length);
  panda_set_checksum(spidev->tx_buffer, pt.tx_length);
  retval = spidev_sync_write(spidev, pt.tx_length+1);

  // wait for ack
  retval = panda_wait_for_ack(spidev, SPI_DACK);
  if (retval < 0) {
    dev_dbg(&spi->dev, "no data ack\n");
    goto end;
  }

  // get response
  retval = spidev_sync_read(spidev, 2);
  uint16_t rlen = (spidev->rx_buffer[1] << 8) | (spidev->rx_buffer[0]);
  dev_dbg(&spi->dev, "rlen %u\n", rlen);
  if (rlen > pt.rx_length_max) {
    dev_dbg(&spi->dev, "RX len greater than max\n");
    retval = -1;
    goto end;
  }

  // do the read
  retval = spidev_sync_read(spidev, rlen);
  retval = copy_to_user((u8 __user *)(uintptr_t)pt.rx_buf, spidev->rx_buffer, rlen);
  if (panda_check_checksum(spidev->rx_buffer, rlen) != 0) {
    dev_dbg(&spi->dev, "bad checksum\n");
    retval = -1;
    goto end;
  } 
  retval = rlen;

end:
  return retval;
}