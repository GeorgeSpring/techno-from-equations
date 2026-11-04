"""song.py → out/stems/*.wav + out/mix.wav.

Every sample is computed from formulas: no samples, no presets, no plugins.
The rhythm functions are used directly as volume envelopes — the graph is the sound."""

import os
import random
from beat import *
import song as S

SR = 44100
SPB = 60 / S.BPM                      # seconds per beat
BEATS = 4 * S.BARS
N = int((BEATS + 1) * SPB * SR)       # +1 beat for the tail
GAIN = {'kick': 1.0, 'clap': 0.5, 'hat': 0.18, 'bass': 0.7, 'acid': 0.3}
HERE = os.path.dirname(os.path.abspath(__file__))


class Filter:
    """Chamberlin state-variable filter: lowpass, bandpass and highpass at once.
    q = 1/resonance: 1.4 is soft, 0.15 screams."""

    def __init__(self):
        self.lp = self.bp = self.hp = 0.0

    def __call__(self, x, cutoff, q):
        f = 2 * sin(pi * min(cutoff, SR / 7) / SR)   # above SR/7 it blows up
        self.lp += f * self.bp
        self.hp = x - self.lp - q * self.bp
        self.bp += f * self.hp
        return self


def env(name, x):
    return getattr(S, name)(x) if S.playing(name, x) else 0.0


def main():
    random.seed(1)
    tanh = math.tanh
    dx = 1 / (SPB * SR)               # beats per sample
    out = {n: [0.0] * N for n in GAIN}
    f_clap, f_hat, f_bass, f_acid = Filter(), Filter(), Filter(), Filter()

    k_prev = k_since = k_ph = 0.0
    b_prev = b_ph = b_amp = 0.0
    b_f = hz(S.ROOT)
    a_prev = a_ph = a_amp = 0.0
    a_f = a_to = hz(S.ROOT)

    for i in range(N):
        x = i * dx
        noise = 2 * random.random() - 1

        # kick: a sine whose pitch falls exponentially after each hit, driven through tanh
        k = env('kick', x)
        if k - k_prev > JUMP:
            k_since = k_ph = 0.0
        k_prev, k_since = k, k_since + dx
        k_ph += 2 * pi * (47 + 170 * exp(-14 * k_since)) / SR
        out['kick'][i] = tanh(2.5 * sin(k_ph)) * k

        # sidechain: everything else ducks under the kick's own curve
        duck = 1 - 0.75 * k

        # clap and hat: filtered noise, shaped by their rhythm functions
        out['clap'][i] = 3 * f_clap(noise, 1200, 0.8).bp * env('clap', x)
        out['hat'][i] = f_hat(noise, 6000, 1.0).hp * env('hat', x)

        # bass: saw + sine, the note is taken from bass_note at each hit
        b = env('bass', x)
        if b - b_prev > JUMP:
            b_f = hz(S.ROOT + snap(S.bass_note(x), S.SCALE))
        b_prev = b
        b_amp += (b - b_amp) * 0.02                   # ~1 ms smoothing: no clicks
        b_ph = (b_ph + b_f / SR) % 1
        saw = 2 * b_ph - 1 + 0.6 * sin(2 * pi * b_ph)
        out['bass'][i] = tanh(1.5 * f_bass(saw, 200 + 1200 * b, 0.7).lp) * b_amp * duck

        # acid: saw with a glide into a screaming resonant lowpass
        a = env('acid', x)
        if a - a_prev > JUMP:
            a_to = hz(S.ROOT + 12 + snap(S.acid_note(x), S.SCALE))
        a_prev = a
        a_f += (a_to - a_f) * 0.004                   # the 303-style slide
        a_amp += (a - a_amp) * 0.02
        a_ph = (a_ph + a_f / SR) % 1
        lp = f_acid(2 * a_ph - 1, S.cutoff(x) * (0.5 + a), 0.15).lp
        out['acid'][i] = tanh(2 * lp) * a_amp * duck

        if i % int(4 * SPB * SR) == 0:
            print(f'\rbar {min(int(x / 4) + 1, S.BARS)}/{S.BARS}', end='', flush=True)
    print()

    # mix, then scale everything so the mix peaks at −1 dB; stems keep the same scale
    mix = [sum(GAIN[n] * out[n][i] for n in GAIN) for i in range(N)]
    scale = 0.89 / max(abs(s) for s in mix)
    os.makedirs(os.path.join(HERE, 'out', 'stems'), exist_ok=True)
    for n in GAIN:
        write_wav(os.path.join(HERE, 'out', 'stems', n + '.wav'),
                  [s * GAIN[n] * scale for s in out[n]], SR)
    # soft limiter on the mix: tanh squeezes the peaks, the rest gets ~6 dB louder
    write_wav(os.path.join(HERE, 'out', 'mix.wav'),
              [tanh(2 * s * scale) / tanh(2) for s in mix], SR)
    print(f'→ out/mix.wav and out/stems/  ({N / SR:.1f} s)')


if __name__ == '__main__':
    main()
