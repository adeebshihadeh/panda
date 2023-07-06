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