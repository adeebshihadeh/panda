struct spi_transfer {
  uint8_t endpoint,
  uint8_t *tx_data,
  uint16_t tx_len,
  uint8_t *rx_data,
  uint16_t max_rx_len,
  unsigned int timeout,
};
