# -*- coding: utf-8 -*-
"""Regenerate the two extra sound effects this episode needs.

  build/sfx/motor.wav - the toy motor whirr (a small DC motor under load)
  build/sfx/swish.wav - the paper side brush sweeping the floor

The pipeline's built-in SFX set (ding / whoosh / beep / chime) has neither,
so this episode ships its own.  Both are short, soft and fade in and out so
they never click.  Run once before s5_audio.py:

    python make_sfx.py
"""
import os
import wave

import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "sfx")


def motor():
    """A soft buzzy whirr: sawtooth stack with a slow wobble + gear rattle."""
    n = int(1.30 * SR)
    t = np.arange(n) / SR
    rng = np.random.RandomState(3)
    wob = 1.0 + 0.05 * np.sin(2 * np.pi * 7.5 * t) + 0.03 * np.sin(2 * np.pi * 13.0 * t)
    ph = 2 * np.pi * np.cumsum(112.0 * wob) / SR
    sig = np.zeros(n)
    for k, amp in ((1, 1.0), (2, 0.55), (3, 0.38), (4, 0.26),
                   (5, 0.18), (7, 0.10), (9, 0.06)):
        sig += amp * np.sin(k * ph)
    sig /= np.linalg.norm(sig) * 0.5
    sig = sig + rng.randn(n) * 0.05 * np.sin(2 * np.pi * 420 * t)
    env = np.minimum(1.0, t / 0.05) * np.minimum(1.0, (n / SR - t) / 0.10)
    return sig * env


def swish():
    """A paper brush sweeping the floor: band-passed noise with a slow whoosh."""
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    rng = np.random.RandomState(11)
    x = rng.randn(n)
    # two one-pole low passes -> band-limited noise, then a high pass for "paper"
    lp1 = np.zeros(n)
    lp2 = np.zeros(n)
    for i in range(n):
        lp1[i] = lp1[i - 1] * 0.86 + x[i] * 0.14 if i else x[i] * 0.14
        lp2[i] = lp2[i - 1] * 0.62 + lp1[i] * 0.38 if i else lp1[i] * 0.38
    hp = x - lp1
    sig = 0.75 * lp2 + 0.45 * hp
    # the brush swings back and forth, so the noise swells and fades
    env = np.sin(np.pi * np.arange(n) / n) ** 1.5
    env = env * (0.72 + 0.28 * np.sin(2 * np.pi * 5.0 * t))
    return sig * env


def write(name, sig, peak=0.55):
    path = os.path.join(OUT, name)
    data = (np.clip(sig / (np.abs(sig).max() + 1e-9) * peak, -1, 1) * 32767).astype(np.int16)
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(data.tobytes())
    w.close()
    print("wrote", path, "%.2fs" % (len(data) / SR))


def main():
    os.makedirs(OUT, exist_ok=True)
    write("motor.wav", motor(), 0.62)
    write("swish.wav", swish(), 0.48)


if __name__ == "__main__":
    main()
