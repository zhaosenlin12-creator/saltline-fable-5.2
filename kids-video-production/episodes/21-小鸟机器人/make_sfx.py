# -*- coding: utf-8 -*-
"""Regenerate the two extra sound effects this episode needs.

  build/sfx/chirp.wav - the little bird call ("啾啾")
  build/sfx/flap.wav  - the paper wings beating

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


def chirp():
    """A bird call: three short whistle notes that slide up, then fall."""
    n = int(0.62 * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    # three little whistles, each a sine with a fast pitch slide
    notes = [(0.00, 0.16, 1500, 2350),
             (0.19, 0.16, 1450, 2250),
             (0.38, 0.20, 1650, 1150)]
    for start, dur, f0, f1 in notes:
        i0 = int(start * SR)
        i1 = min(n, i0 + int(dur * SR))
        m = i1 - i0
        if m <= 0:
            continue
        lt = np.arange(m) / float(m)
        freq = f0 + (f1 - f0) * lt
        ph = 2 * np.pi * np.cumsum(freq) / SR
        note = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.16 * np.sin(3 * ph)
        env = np.sin(np.pi * lt) ** 1.4
        sig[i0:i1] += note * env
    sig /= np.linalg.norm(sig) * 0.5
    return sig


def flap():
    """Paper wings beating: soft filtered noise, one swish per beat."""
    n = int(0.70 * SR)
    t = np.arange(n) / SR
    rng = np.random.RandomState(21)
    x = rng.randn(n)
    # two one-pole low passes -> soft noise, then a touch of high "paper"
    lp1 = np.zeros(n)
    lp2 = np.zeros(n)
    for i in range(n):
        lp1[i] = lp1[i - 1] * 0.80 + x[i] * 0.20 if i else x[i] * 0.20
        lp2[i] = lp2[i - 1] * 0.58 + lp1[i] * 0.42 if i else lp1[i] * 0.42
    hp = x - lp1
    sig = 0.80 * lp2 + 0.30 * hp
    # three beats of wings
    env = np.zeros(n)
    for k, start in enumerate((0.02, 0.26, 0.48)):
        i0 = int(start * SR)
        m = int(0.16 * SR)
        seg = np.sin(np.pi * np.arange(m) / float(m)) ** 1.6
        env[i0:i0 + m] += seg * (1.0 - 0.18 * k)
    env = np.clip(env, 0, 1)
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
    write("chirp.wav", chirp(), 0.55)
    write("flap.wav", flap(), 0.42)


if __name__ == "__main__":
    main()
