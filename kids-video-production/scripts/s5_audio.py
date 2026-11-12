# -*- coding: utf-8 -*-
"""s5_audio.py - synthesise BGM + SFX, lay the narration down, and mix.

The music bed is generated with numpy so it is royalty-free and can be tuned
per project: BPM, chord progression and the melody are all project settings.
Duck the music under the voice, then limit.

Project settings read from project.py:
    BPM, CHORDS, MELODY, SFX_CUES, BGM_GAIN, DUCK_DEPTH
"""
import os
import json
import wave

import numpy as np

from common import load_project, load_json

SR = 44100


def MIDI(m):
    return 440.0 * (2 ** ((m - 69) / 12.0))


def add(buf, t0, sig):
    s = int(t0 * SR)
    n = min(len(sig), len(buf) - s)
    if n > 0:
        buf[s:s + n] += sig[:n]


def tone(freq, dur, harmonics, attack=0.004, decay=None, curve=3.0):
    n = int(dur * SR)
    i = np.arange(n) / SR
    w = np.zeros(n)
    for k, h in enumerate(harmonics):
        w += h * np.sin(2 * np.pi * freq * (k + 1) * i)
    w /= max(sum(harmonics), 1e-9)
    env = np.exp(-curve * i / (decay if decay else dur))
    a = max(1, int(attack * SR))
    env[:a] *= np.linspace(0, 1, a)
    return w * env


def noise_burst(dur, decay, lp=0.5, hp=0.0):
    n = int(dur * SR)
    x = np.random.randn(n)
    if lp < 1.0:
        prev, out = 0.0, np.zeros(n)
        for j in range(n):
            prev = prev * (1 - lp) + x[j] * lp
            out[j] = prev
        x = out * 3.0
    if hp > 0:
        prev, out = 0.0, np.zeros(n)
        for j in range(n):
            prev = prev * (1 - hp) + x[j] * hp
            out[j] = x[j] - prev
        x = out
    return x * np.exp(-np.arange(n) / SR / decay)


def build_bgm(total, bpm, chords, melody):
    beat = 60.0 / bpm
    bar = beat * 4
    n = int(total * SR) + SR
    pad = np.zeros(n); bass = np.zeros(n); pluck = np.zeros(n)
    mel = np.zeros(n); perc = np.zeros(n)
    cycle = bar * 4
    for c in range(int(np.ceil(total / cycle))):
        t0 = c * cycle
        for ci, (root, tones) in enumerate(chords):
            bt = t0 + ci * bar
            for t in tones:
                add(pad, bt, tone(MIDI(t), bar * 1.02, (1.0, 0.22, 0.10),
                                  attack=0.22, curve=0.9) * 0.075)
            add(bass, bt, tone(MIDI(root - 12), beat * 1.6, (1.0, 0.08),
                               attack=0.006, decay=0.55) * 0.16)
            add(bass, bt + beat * 2, tone(MIDI(root), beat * 1.2, (1.0, 0.08),
                                          attack=0.006, decay=0.42) * 0.11)
            for k, pi in enumerate([0, 1, 2, 1, 0, 2, 1, 2]):
                add(pluck, bt + k * beat / 2,
                    tone(MIDI(tones[pi] + 12), beat * 0.8, (1.0, 0.22, 0.06),
                         attack=0.002, decay=0.16) * 0.13)
            for k in range(4):
                add(perc, bt + k * beat + beat / 2,
                    noise_burst(0.05, 0.018, lp=0.85, hp=0.72) * 0.055)
            for k in (1, 3):
                add(perc, bt + k * beat,
                    tone(1180, 0.09, (1.0,), attack=0.001, decay=0.035) * 0.035)
        for (b, m, ln) in melody:
            tt = t0 + b * beat
            if tt <= total:
                add(mel, tt, tone(MIDI(m), ln * beat * 1.6, (1.0, 0.45, 0.22, 0.10),
                                  attack=0.003, decay=0.55) * 0.085)
    bgm = pad + bass + pluck + mel + perc
    env = np.abs(bgm)
    thr = 0.32
    over = env > thr
    bgm[over] = np.sign(bgm[over]) * (thr + (env[over] - thr) * 0.45)
    fi, fo = int(1.2 * SR), int(2.4 * SR)
    bgm[:fi] *= np.linspace(0, 1, fi)
    bgm[-fo:] *= np.linspace(1, 0, fo)
    return bgm[:int(total * SR)]


def sfx_ding():
    """Two-tone chime: a bright bell for section changes."""
    out = np.zeros(int(0.95 * SR))
    for k, f in enumerate((1568, 2349, 3136)):
        t = tone(f, 0.9, (1.0, 0.45, 0.2), attack=0.001, decay=0.42) * 0.45
        o = int(k * 0.02 * SR)
        out[o:o + len(t)] += t
    base = tone(784, 0.9, (1.0,), attack=0.001, decay=0.3) * 0.22
    out[:len(base)] += base
    return out / 1.4


def sfx_whoosh():
    """Filtered noise sweep for a transition."""
    n = int(0.45 * SR)
    out = np.zeros(n)
    prev = 0.0
    rnd = np.random.RandomState(7)
    for j in range(n):
        prev = prev * 0.98 + rnd.randn() * 0.02
        out[j] = prev
    env = np.sin(np.pi * np.arange(n) / n) ** 1.6
    return out * env * 0.9


def sfx_beep():
    """Two short blips: the moment the program starts."""
    out = np.zeros(int(0.32 * SR))
    a = tone(980, 0.10, (1.0, 0.3), attack=0.002, decay=0.05)
    b = tone(1320, 0.12, (1.0, 0.3), attack=0.002, decay=0.06)
    out[0:len(a)] += a
    out[int(0.14 * SR):int(0.14 * SR) + len(b)] += b
    return out * 0.55


def sfx_chime():
    """Ascending arpeggio for the ending."""
    out = np.zeros(int(1.4 * SR))
    for k, f in enumerate((784, 988, 1319)):
        t = tone(f, 1.1, (1.0, 0.35, 0.14), attack=0.002, decay=0.5) * 0.7
        o = int(k * 0.13 * SR)
        out[o:o + len(t)] += t
    return out


def read_wav(path):
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return a, sr


def resample(a, src, dst):
    if src == dst:
        return a
    n = int(len(a) * dst / src)
    idx = np.linspace(0, len(a) - 1, n)
    return np.interp(idx, np.arange(len(a)), a)


def main():
    p = load_project()
    aud = os.path.join(p.BUILD, "audio")
    os.makedirs(aud, exist_ok=True)
    tl = load_json(os.path.join(p.BUILD, "timeline.json"))
    total = tl["total"]
    n_total = int((total + 1.2) * SR)

    nar = np.zeros(n_total)
    for ln in tl["lines"]:
        a, sr = read_wav(ln["wav"])
        a = resample(a, sr, SR)
        s = int(ln["start"] * SR)
        e = min(n_total, s + len(a))
        nar[s:e] += a[:e - s]

    bgm_file = getattr(p, "BGM_FILE", None)
    if bgm_file:
        ba, bsr = read_wav(os.path.join(p.ROOT, bgm_file))
        bgm = resample(ba, bsr, SR)[:n_total]
        print("  custom bgm:", bgm_file)
    else:
        bgm = build_bgm(total + 1.15, p.BPM, p.CHORDS, p.MELODY)[:n_total]
    if len(bgm) < n_total:
        bgm = np.pad(bgm, (0, n_total - len(bgm)))

    sfx = np.zeros(n_total)
    np.random.seed(11)

    def put(sig, t0, amp):
        s = int(t0 * SR)
        e = min(n_total, s + len(sig))
        if e > s:
            sfx[s:e] += sig[:e - s] * amp

    sounds = {"ding": sfx_ding(), "whoosh": sfx_whoosh(),
              "beep": sfx_beep(), "chime": sfx_chime()}
    for _nm, _rel in (getattr(p, "SFX_EXTRA", {}) or {}).items():
        try:
            _a, _sr = read_wav(os.path.join(p.ROOT, _rel))
            sounds[_nm] = resample(_a, _sr, SR)
            print("  extra sfx:", _nm, _rel)
        except Exception as _e:
            print("  extra sfx skipped:", _nm, _e)
    # SFX cues are anchored to narration lines, not absolute seconds, so the
    # sound effects stay in sync when the TTS run comes out a little longer
    # or shorter than the previous one.
    #   ("L12", 0.0, 0.40)  ->  at the start of line L12
    #   ("L13", 1.5, 0.16)  ->  1.5s into line L13
    starts = {ln["id"]: ln["start"] for ln in tl["lines"]}
    for name, cues in p.SFX_CUES.items():
        for cue in cues:
            if len(cue) == 3:
                line_id, offset, amp = cue
                t = starts.get(line_id)
                if t is None:
                    continue
                t += offset
            else:                       # legacy (time, amp)
                t, amp = cue
            put(sounds[name], t, amp)

    win = int(0.02 * SR)
    nb = len(nar) // win
    lvl = np.sqrt((nar[:nb * win].reshape(nb, win) ** 2).mean(axis=1))
    lvl = lvl / (lvl.max() + 1e-9)
    sm = np.convolve(lvl, np.ones(15) / 15, mode="same")
    duck = 1.0 - p.DUCK_DEPTH * np.clip(sm, 0, 1)
    duck = np.interp(np.arange(len(nar)) / win, np.arange(nb), duck).astype(np.float32)

    mix = nar * 0.92 + bgm * duck * p.BGM_GAIN + sfx
    peak = np.abs(mix).max()
    if peak > 0.97:
        mix = mix / peak * 0.97
    mix = np.tanh(mix * 1.06) * 0.96

    st = (np.clip(np.stack([mix, mix], axis=1), -1, 1) * 32767).astype(np.int16)
    out = os.path.join(aud, "mix.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(st.tobytes())
    for name, sig in sounds.items():
        with wave.open(os.path.join(aud, "sfx_%s.wav" % name), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(sig, -1, 1) * 32767).astype(np.int16).tobytes())
    print("audio: %.2fs  narration_peak=%.3f  mix_peak=%.3f" %
          (total, np.abs(nar).max(), np.abs(mix).max()))
    print("wrote", out)


if __name__ == "__main__":
    main()
