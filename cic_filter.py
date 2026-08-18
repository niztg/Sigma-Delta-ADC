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
