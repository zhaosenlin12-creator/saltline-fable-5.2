# -*- coding: utf-8 -*-
"""Regenerate build/sfx/pop.wav - the soft cardboard 啪 used by this episode.

The pipeline's built-in SFX set (ding / whoosh / beep / chime) has no
"pop", so this episode ships its own.  The sound is deliberately harmless
and cardboard-like: a short filtered noise slap, a low body thump and a
very short high tick - it reads as a paper disc being tapped, not a blast.

Run it once before s5_audio.py:

    python make_pop_sfx.py            # writes build/sfx/pop.wav
"""
import os
import wave

import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "sfx", "pop.wav")


def build():
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    rng = np.random.RandomState(5)

    # filtered noise slap
    raw = rng.randn(n)
    prev, out = 0.0, np.zeros(n)
    for i in range(n):
        prev = prev * 0.55 + raw[i] * 0.45
        out[i] = prev
    sig = out * np.exp(-t / 0.035) * 0.8

    # low body thump with a fast pitch drop
    f = 220 * np.exp(-t * 9) + 90
    sig = sig + np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09) * 0.55

    # very short high tick for definition
    sig = sig + np.sin(2 * np.pi * 1400 * t) * np.exp(-t / 0.012) * 0.18

    sig = sig / (np.abs(sig).max() + 1e-9) * 0.85
    return (np.clip(sig, -1, 1) * 32767).astype(np.int16)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    w = wave.open(OUT, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(build().tobytes())
    w.close()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
