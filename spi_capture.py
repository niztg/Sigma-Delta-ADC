import spidev
import time
import numpy as np

SPI_BUS        = 0
SPI_DEVICE     = 0
SPI_CLOCK_HZ   = 51_200
CAPTURE_SECS   = 1.0
BYTES_PER_XFER = 64

def open_spi(bus, device, clock_hz):
    spi = spidev.SpiDev()
    spi.open(bus, device)
    spi.max_speed_hz = clock_hz
    spi.mode = 0b00
    spi.bits_per_word = 8
    spi.no_cs = False
    return spi