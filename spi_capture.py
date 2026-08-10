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

def capture_bitstream(spi, duration_s, bytes_per_xfer):
    raw_bytes = []
    dummy = [0x00] * bytes_per_xfer # zeroes to send out on the (unused) MOSI pin
    t_start = time.monotonic()
    while time.monotonic() - t_start < duration_s: # loops until one second has elapsed
        raw_bytes.extend(spi.xfer2(dummy)) # queues the last 8 bytes from the MISO pin
    return np.array(raw_bytes, dtype=np.uint8)

