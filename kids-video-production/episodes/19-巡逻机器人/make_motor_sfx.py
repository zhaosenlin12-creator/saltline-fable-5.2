# -*- coding: utf-8 -*-
"""Regenerate build/sfx/motor.wav - the toy motor whirr used by this episode.

The pipeline's built-in SFX set (ding / whoosh / beep / chime) has no motor
sound, so this episode ships its own.  It is a soft buzzy whirr - a stack
of sawtooth harmonics with a slow wobble plus a faint gear rattle - so it
reads as a small DC motor, not a power tool.

Run it once before s5_audio.py:

    python make_motor_sfx.py            # writes build/sfx/motor.wav
"""
import os
import wave

import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "sfx", "motor.wav")


def build():
    n = int(1.30 * SR)
    t = np.arange(n) / SR
    rng = np.random.RandomState(3)

    # slow speed wobble, like a cheap motor under load
    wob = 1.0 + 0.05 * np.sin(2 * np.pi * 7.5 * t) + 0.03 * np.sin(2 * np.pi * 13.0 * t)
    ph = 2 * np.pi * np.cumsum(112.0 * wob) / SR

    sig = np.zeros(n)
    for k, amp in ((1, 1.0), (2, 0.55), (3, 0.38), (4, 0.26),
                   (5, 0.18), (7, 0.10), (9, 0.06)):
        sig += amp * np.sin(k * ph)
    sig /= np.linalg.norm(sig) * 0.5

    # faint gear rattle
    sig = sig + rng.randn(n) * 0.05 * np.sin(2 * np.pi * 420 * t)

    # fade in and out so it never clicks
    env = np.minimum(1.0, t / 0.05) * np.minimum(1.0, (n / SR - t) / 0.10)
    sig = sig * env
    return (np.clip(sig / (np.abs(sig).max() + 1e-9) * 0.62, -1, 1) * 32767).astype(np.int16)


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
