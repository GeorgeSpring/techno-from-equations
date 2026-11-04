"""The small toolbox behind song.py: math shortcuts, scales, hit detection,
and tiny MIDI / WAV writers. Standard library only — nothing to install."""

import math
import struct
import wave

# ── math vocabulary ──────────────────────────────────────────────────────────

sin, cos, exp, pi = math.sin, math.cos, math.exp, math.pi


def mod(x, m=1.0):
    """mod(x, m) — the sawtooth everything is built on: 0 → m, then back to 0."""
    return x % m


def fl(x):
    """⌊x⌋ — turns smooth curves into steps."""
    return math.floor(x)


def spike(x, period=1.0, offset=0.0, decay=6.0):
    """e^(−decay · mod(x − offset, period)): jumps to 1 at `offset`, then decays.
    Repeats every `period` beats. This is a drum hit."""
    return exp(-decay * ((x - offset) % period))


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


# ── scales ───────────────────────────────────────────────────────────────────

MINOR = [0, 2, 3, 5, 7, 8, 10]
PHRYGIAN = [0, 1, 3, 5, 7, 8, 10]   # darker: the flat 2nd
DORIAN = [0, 2, 3, 5, 7, 9, 10]


def snap(semis, scale):
    """Round any number of semitones to the nearest note of the scale."""
    octave = math.floor(semis / 12)
    notes = [12 * o + d for o in (octave - 1, octave, octave + 1) for d in scale]
    return min(notes, key=lambda n: abs(n - semis))


def hz(midi_note):
    return 440.0 * 2 ** ((midi_note - 69) / 12)


# ── hits: where the curve jumps up ───────────────────────────────────────────

JUMP = 0.3   # how far the curve must jump to count as a hit


def hits(f, beats, grid=0.25):
    """Scan f on a 16th-note grid; a hit is where f jumps up by more than JUMP.
    Yields (beat, velocity 0..1)."""
    for i in range(int(beats / grid)):
        x = i * grid
        y, before = f(x), f(x - 1e-3)
        if y - before > JUMP:
            yield x, clamp(y)


# ── MIDI writer (Standard MIDI File, type 1) ─────────────────────────────────

def _vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append(0x80 | (n & 0x7F))
        n >>= 7
    return bytes(reversed(out))


def _chunk(tag, data):
    return tag + struct.pack('>I', len(data)) + data


def write_midi(path, bpm, tracks, ppq=480):
    """tracks: list of (name, channel 0..15, events).
    event: (beat, 'on', note, velocity 1..127) | (beat, 'off', note, 0) | (beat, 'cc', number, value)."""
    tempo = round(60_000_000 / bpm)
    head = _chunk(b'MThd', struct.pack('>HHH', 1, len(tracks) + 1, ppq))
    conductor = b'\x00\xFF\x51\x03' + tempo.to_bytes(3, 'big') + b'\x00\xFF\x2F\x00'
    chunks = [head, _chunk(b'MTrk', conductor)]
    order = {'off': 0, 'cc': 1, 'on': 2}           # at the same tick: release first
    for name, ch, events in tracks:
        data = bytearray(b'\x00\xFF\x03' + _vlq(len(name.encode())) + name.encode())
        now = 0
        for beat, kind, a, b in sorted(events, key=lambda e: (e[0], order[e[1]])):
            tick = round(beat * ppq)
            status = {'on': 0x90, 'off': 0x80, 'cc': 0xB0}[kind] | ch
            data += _vlq(tick - now) + bytes([status, a, b])
            now = tick
        data += b'\x00\xFF\x2F\x00'
        chunks.append(_chunk(b'MTrk', bytes(data)))
    with open(path, 'wb') as fh:
        fh.write(b''.join(chunks))


# ── WAV writer (16-bit mono) ─────────────────────────────────────────────────

def write_wav(path, samples, sr):
    frames = struct.pack('<%dh' % len(samples),
                         *(int(32767 * clamp(s, -1, 1)) for s in samples))
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(frames)
