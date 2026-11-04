"""The whole track lives in this file.

x is time in beats (x = 0, 1, 2, … are the kicks of a 4/4 bar).
Change a formula, run make_midi.py or make_wav.py, and hear what it does."""

from beat import *

BPM = 140
BARS = 16
ROOT = 45          # MIDI note: A2. Everything below is in semitones above it
SCALE = MINOR

# ── rhythm ───────────────────────────────────────────────────────────────────
# The value is the volume. A note fires wherever the curve jumps up.

def kick(x):   # y = e^(−6·mod(x,1)): a spike on every beat — four on the floor
    return spike(x, 1, 0, 6)

def clap(x):   # period 2, shifted by 1 beat: lands on beats 2 and 4
    return spike(x, 2, 1, 18)

def hat(x):    # loud offbeat + quiet sixteenths
    return spike(x, 1, 0.5, 30) + 0.35 * spike(x, 0.25, 0, 70)

def bass(x):   # rolling bass: three sixteenths after each kick, never on it
    return spike(x, 0.25, 0, 14) * (mod(x, 1) >= 0.25)

def acid(x):   # every 3rd sixteenth is silent → a 3-beat loop against the 4-beat bar
    return spike(x, 0.25, 0, 5) * (mod(fl(4 * x), 3) != 2)

# ── pitch ────────────────────────────────────────────────────────────────────
# Semitones above ROOT; snapped to SCALE before they are played.

def bass_note(x):   # home for 4 beats, down a fourth for 2, up an octave for 2
    return 5 * fl(mod(x, 8) / 4) + 7 * fl(mod(x, 8) / 6) - 12

def acid_note(x):   # |sin|: sweeps up the scale and back every 4 beats
    return 12 * abs(sin(pi * x / 4))

# ── modulation ───────────────────────────────────────────────────────────────

def cutoff(x):      # acid filter in Hz: opens like x² over 2 bars, then snaps shut
    return 300 + 3500 * mod(x / 8, 1) ** 2

# ── arrangement: bars where each part plays [from, to) ───────────────────────

PARTS = {
    'kick': (0, 16),
    'hat':  (2, 16),
    'clap': (4, 16),
    'bass': (4, 16),
    'acid': (8, 16),
}

def playing(part, x):
    a, b = PARTS[part]
    return 4 * a <= x < 4 * b
