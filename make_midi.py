"""song.py → out/song.mid: one MIDI track per part, ready to drop into any DAW.

The rhythm functions decide where notes go and how hard (velocity),
the pitch functions decide which note, the cutoff curve becomes CC74."""

import os
from beat import *
import song as S

BEATS = 4 * S.BARS
DRUMS = 9            # MIDI channel 10 (counted from 0): General MIDI drums
HERE = os.path.dirname(os.path.abspath(__file__))


def part(name):
    """the part's rhythm function, silent outside its bars"""
    f = getattr(S, name)
    return lambda x: f(x) if S.playing(name, x) else 0.0


def vel(v):
    return max(1, round(127 * v))


def drum(name, note):
    ev = []
    for x, v in hits(part(name), BEATS):
        ev += [(x, 'on', note, vel(v)), (x + 0.2, 'off', note, 0)]
    return name.capitalize(), DRUMS, ev


def synth(name, pitch, channel, length=0.2):
    ev = []
    for x, v in hits(part(name), BEATS):
        n = S.ROOT + snap(pitch(x), S.SCALE)
        ev += [(x, 'on', n, vel(v)), (x + length, 'off', n, 0)]
    return name.capitalize(), channel, ev


def cc_lane(f, number, lo=100.0, hi=8000.0, step=0.125):
    """a curve in Hz → CC values, on a log scale like a cutoff knob"""
    ev = []
    for i in range(int(BEATS / step)):
        x = i * step
        v = clamp(math.log(f(x) / lo) / math.log(hi / lo))
        ev.append((x, 'cc', number, round(127 * v)))
    return ev


def main():
    tracks = [
        drum('kick', 36),
        drum('clap', 39),
        drum('hat', 42),
        synth('bass', S.bass_note, 0),
        synth('acid', S.acid_note, 1),
    ]
    tracks[-1][2].extend(cc_lane(S.cutoff, 74))     # CC74 = filter cutoff

    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    path = os.path.join(HERE, 'out', 'song.mid')
    write_midi(path, S.BPM, tracks)
    for name, _, ev in tracks:
        print(f'{name:5} {sum(e[1] == "on" for e in ev):4} notes')
    print(f'→ {os.path.relpath(path)}  ({S.BARS} bars at {S.BPM} BPM)')


if __name__ == '__main__':
    main()
