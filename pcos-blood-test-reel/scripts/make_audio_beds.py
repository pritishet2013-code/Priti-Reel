"""Synthesises the royalty-free background music bed and the soft 'pop' SFX.

Usage: python3 make_audio_beds.py <out_dir> <duration_seconds> <sfx_times.json>
Writes music.wav (light, upbeat educational bed) and sfx.wav (pops at given times).
Everything is generated here, so there are no licensing concerns.
"""
import json
import sys
import wave

import numpy as np

SR = 48000
out_dir, dur, sfx_json = sys.argv[1], float(sys.argv[2]), sys.argv[3]
N = int(SR * (dur + 0.5))
rng = np.random.default_rng(7)


def note(freq):
    return 440.0 * 2 ** ((freq - 69) / 12)


def env(n, a=0.005, d=0.3, sustain=0.0, decay_rate=None):
    t = np.arange(n) / SR
    e = np.minimum(t / a, 1.0)
    if decay_rate:
        e *= np.exp(-t * decay_rate)
    return e


def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def epiano(freq, length, vel=1.0):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t * 6)
         + 0.12 * np.sin(2 * np.pi * 3 * freq * t) * np.exp(-t * 9))
    return s * env(n, a=0.01, decay_rate=1.6) * vel


def pluck(freq, length=0.45, vel=1.0):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * 2 * freq * t + 0.3) * np.exp(-t * 14)
    return s * env(n, a=0.003, decay_rate=9) * vel


def kick():
    n = int(0.28 * SR)
    t = np.arange(n) / SR
    f = 50 + 70 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 13)


def shaker():
    n = int(0.06 * SR)
    s = rng.standard_normal(n)
    s = np.diff(np.concatenate([[0], s]))  # crude high-pass
    return s * np.exp(-np.arange(n) / SR * 70) * 0.25


def bass(freq, length):
    n = int(length * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) + 0.2 * np.sin(2 * np.pi * 2 * freq * t)) * env(n, a=0.01, decay_rate=2.5)


music = np.zeros(N)
bpm = 104
beat = 60 / bpm
bar = 4 * beat
# C – G – Am – F  (bright, friendly)
prog = [(60, [60, 64, 67, 72]), (55, [59, 62, 67, 71]), (57, [60, 64, 69, 72]), (53, [60, 65, 69, 72])]
arp_pat = [0, 2, 1, 3, 2, 1, 3, 2]
t0 = 0.0
k = 0
while t0 < dur + bar:
    root, chord = prog[k % 4]
    for m in chord:
        add(music, t0, epiano(note(m), bar), 0.10)
    add(music, t0, bass(note(root - 12), beat * 1.8), 0.22)
    add(music, t0 + 2 * beat, bass(note(root - 12), beat * 1.8), 0.18)
    for i in range(8):
        add(music, t0 + i * beat / 2, pluck(note(chord[arp_pat[i]] + 12)), 0.07)
        add(music, t0 + i * beat / 2 + beat / 4 * (i % 2), shaker(), 0.5)
    for b in (0, 2):
        add(music, t0 + b * beat, kick(), 0.35)
    t0 += bar
    k += 1

# gentle fades
fade_in, fade_out = int(0.6 * SR), int(1.2 * SR)
end = int(dur * SR)
music[:fade_in] *= np.linspace(0, 1, fade_in)
music[end - fade_out:end] *= np.linspace(1, 0, fade_out)
music[end:] = 0
music /= np.max(np.abs(music)) + 1e-9
music *= 0.9

# soft "pop" for text appearances
sfx = np.zeros(N)
n = int(0.09 * SR)
t = np.arange(n) / SR
pop = np.sin(2 * np.pi * np.cumsum(900 - 500 * t / t[-1]) / SR) * np.exp(-t * 55)
for ts in json.load(open(sfx_json)):
    add(sfx, ts, pop, 0.8)
sfx = np.clip(sfx, -1, 1)


def write(path, x):
    x = np.clip(x, -1, 1)
    data = (x * 32767).astype('<i2')
    stereo = np.repeat(data[:, None], 2, axis=1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


write(f'{out_dir}/music.wav', music)
write(f'{out_dir}/sfx.wav', sfx)
print('wrote music.wav and sfx.wav')
