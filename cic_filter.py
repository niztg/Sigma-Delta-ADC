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