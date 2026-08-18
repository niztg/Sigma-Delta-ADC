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


def unpack_bits(raw):
    return np.unpackbits(raw)

def print_bitstream_stats(bits: np.ndarray, elapsed_s: float) -> None:
    n_bits    = len(bits)
    ones      = np.sum(bits)
    zeros     = n_bits - ones
    density   = ones / n_bits          # ≈ (Vin − Vref_low) / (Vref_high − Vref_low)
    bit_rate  = n_bits / elapsed_s

    print(f"\n── Bitstream capture report ──────────────────────────────")
    print(f"  Total bits captured : {n_bits:,}")
    print(f"  Elapsed time        : {elapsed_s:.4f} s")
    print(f"  Measured bit rate   : {bit_rate:,.1f} Hz  (target: {SPI_CLOCK_HZ:,} Hz)")
    print(f"  Ones                : {ones:,}  ({100*ones/n_bits:.2f}%)")
    print(f"  Zeros               : {zeros:,}  ({100*zeros/n_bits:.2f}%)")
    print(f"  Ones density        : {density:.5f}  → Vin ≈ {density*5.0:.4f} V (if Vref=1.65V, supply=3V)")
    print(f"──────────────────────────────────────────────────────────\n")

    # First 64 bits as a visual sanity check
    print("  First 64 bits: ", "".join(str(b) for b in bits[:64]))
    print()

def main():
    spi = open_spi(SPI_BUS, SPI_DEVICE, SPI_CLOCK_HZ)

    print(f"SPI opened: bus={SPI_BUS}, device={SPI_DEVICE}, requested clock={SPI_CLOCK_HZ} Hz")
    print(f"Capturing for {CAPTURE_SECS} s...")

    t0  = time.monotonic()
    raw = capture_bitstream(spi, CAPTURE_SECS, BYTES_PER_XFER)
    t1  = time.monotonic()

    spi.close()

    bits = unpack_bits(raw)
    print_bitstream_stats(bits, t1 - t0)

    # Save for offline inspection or filter development
    np.save("bitstream_raw.npy", bits)
    print("Raw bits saved to bitstream_raw.npy")

if __name__ == "__main__":
    main()