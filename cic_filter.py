"""
Design Specs:
Bandwidth:          200 Hz
OSR:                256
Bit rate:           51.2 kHz
Decimation factor:  256
CIC order (N):      3
"""

import numpy as np
import sys

def bits_to_pm1(bits: np.ndarray, invert: bool = True) -> np.ndarray:
    """
    Converts a 0/1 bitstream into -1/1
    invert flag exists due to polarity correction: closed-loop hardware produces an inverse relationship between input voltage and ones density
    invert flag corrects for this
    """
    bits = np.asarray(bits).astype(np.float64)
    if invert:
        bits = 1.0 - bits # turns zeros into ones and ones into zeros

    return 2.0 * bits - 1.0 # map: {0,1} -> {-1,1}

def decimate_cic(bits: np.ndarray, R: int = 256, N: int = 3, invert: bool = True) -> np.ndarray:
    """
    Decimates a noisy bitstream (51.2 kHz) by pulling one out of every R samples.
    Stages:
        1. Low-pass filter: suppress high-frequency noise from the integrators in accordance with Nyquist in order to avoid high frequency being folded in
        2. Downsample by keeping one out of every R samples.
        3. Regularize by R^N to account for the gain factor of each integrator-comb pair
    """

    x = bits_to_pm1(bits, invert=invert)

    for i in range(N):
        x = np.cumsum(x)

    x = x[R-1::R] # take only every Rth sample

    # N cascaded combs
    for i in range(N):
        x = np.diff(x, prepend=x[0] if len(x) else 0.0)

    x = x / (R**N)
    return x

def ones_density_to_estimate(bits: np.ndarray, invert: bool = True) -> float:
    x = bits_to_pm1(bits, invert=invert)
    return float(np.mean(x))

def estimate_to_voltage(estimate: float, V_ref: float = 1.65, full_scale: float = 1.65) -> float:
    return V_ref + estimate * full_scale

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "bitstream_raw.npy"
    bits = np.load(path)
 
    print(f"Loaded {len(bits)} bits from {path}")
 
    # Quick sanity check against spi_capture.py's own reported ones density
    raw_ones_density = float(np.mean(bits))
    print(f"Raw ones density        : {raw_ones_density:.5f}")
 
    quick_est = ones_density_to_estimate(bits, invert=True)
    quick_v = estimate_to_voltage(quick_est)
    print(f"Whole-buffer estimate    : {quick_est:+.5f}  -> Vin ~ {quick_v:.4f} V")
 
    out = decimate_cic(bits, R=256, N=3, invert=True)
    print(f"CIC output: {len(out)} samples at ~200 Hz")
 
    if len(out) > 0:
        voltages = estimate_to_voltage(out)
        print(f"  mean   : {np.mean(out):+.5f}  -> {np.mean(voltages):.4f} V")
        print(f"  std    : {np.std(out):.5f}   (proxy for output noise/ripple)")
        print(f"  min/max: {np.min(out):+.5f} / {np.max(out):+.5f}")
 
        # crude SNR-ish figure: mean-squared signal vs variance around it,
        # useful as a relative number across captures even before a proper
        # SNR measurement with a known sinusoidal input.
        signal_power = np.mean(out) ** 2
        noise_power = np.var(out)
        if noise_power > 0:
            snr_db = 10 * np.log10(signal_power / noise_power) if signal_power > 0 else float("-inf")
            print(f"  crude DC SNR proxy: {snr_db:.1f} dB (mean^2 / variance; "
                  f"not a real AC SNR measurement, just a relative noise indicator)")