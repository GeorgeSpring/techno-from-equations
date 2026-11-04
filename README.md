# techno from equations

**Every sound is a function.** A tiny toolkit behind [@mathbeatlab](https://www.youtube.com/@mathbeatlab):
write a techno track as a handful of math formulas, get **MIDI for your DAW** or **WAV stems synthesized straight from the formulas**: no samples, no presets.

▶ Listen: [`examples/mix.mp3`](examples/mix.mp3) · MIDI: [`examples/song.mid`](examples/song.mid) · stems: [`examples/stems/`](examples/stems)

**No Python? Try it in 30 seconds:** click the green **Code → Download ZIP** button at the top of this page, unzip, and drag `examples/song.mid` and `examples/stems/*.wav` into your DAW at 140 BPM.

```
python3 make_midi.py     # → out/song.mid    (kick, clap, hat, bass, acid + filter CC)
python3 make_wav.py      # → out/mix.wav + out/stems/*.wav
```

Python 3.8+ and the standard library: nothing to install. On Windows, type `python` instead of `python3`.

---

## The idea

Every part of the track is a function of one variable, **x = time in beats** (x = 0, 1, 2, … are the kicks).
There are only three kinds of functions:

| kind | what the value means | example |
|---|---|---|
| **rhythm** | volume; a note fires where the curve **jumps up** | kick `y = e^(−6·mod(x,1))`: a spike on every beat |
| **pitch** | semitones above the root, snapped to the scale | acid `y = 12·\|sin(πx/4)\|`: up the scale and back every 4 beats |
| **modulation** | a knob over time | cutoff `c = 300 + 3500·mod(x/8,1)²`: opens like x² over 2 bars, snaps shut |

`mod(x, 1)` is a sawtooth that restarts on every beat, so `e^(−6·mod(x,1))` jumps to 1 on each beat and decays. That *is* a kick drum's volume envelope. Shift it, change the period, multiply it by a condition, and you get every groove there is:

```python
spike(x, 2, 1, 18)                                  # period 2, shifted by 1 → beats 2 and 4 (clap)
spike(x, 1, 0.5, 30)                                # the offbeat (open hat)
spike(x, 0.25, 0, 14) * (mod(x, 1) >= 0.25)          # rolling bass: 3 sixteenths after each kick
spike(x, 0.25, 0, 5) * (mod(fl(4 * x), 3) != 2)      # every 3rd 16th silent → 3 against 4
```

The whole track is [`song.py`](song.py), about 50 lines. Edit it, re-run, listen.

## More formulas to try

Paste these into `song.py`.

| part | formula | what you hear |
|---|---|---|
| kick | `spike(x,1,0,6) + 0.45*spike(x,1,0.75,30)` | a ghost kick just before every beat |
| kick | `spike(x,2,0,6) + spike(x,2,0.75,6) + spike(x,2,1.5,6)` | 3-3-2: hits on 0, ¾ and 1½ |
| bass_note | `12*fl(mod(x,2)) - 12` | octave jump every 2 beats |
| bass_note | `3*mod(fl(x),4) - 12` | walks up in thirds and resets |
| acid_note | `24*mod(x/4,1)` | a two-octave run every bar |
| acid_note | `mod(7*fl(x),12)` | the circle of fifths as a melody |
| acid_note | `6*(sin(pi*x/2) + sin(pi*x/3)) + 12` | two sines (periods 4 and 6) that only line up every 12 beats |
| acid_note | `24*mod(x*x/32,1)` | x²: the melody speeds up as it goes |
| cutoff | `300 + 3000*abs(sin(pi*x/16))` | the filter breathes |
| cutoff | `400 + 2500*mod(x/4,1)` | sawtooth filter: opens over a bar, snaps shut |

Change `SCALE` to `PHRYGIAN` for a darker sound, and `ROOT`, `BPM`, `BARS` and `PARTS` (the arrangement) at the top and bottom of the file.

## How the sounds are made (`make_wav.py`)

Everything is computed sample by sample:

- **kick**: a sine whose pitch falls exponentially after each hit, `f = 47 + 170·e^(−14·t)` Hz (t in beats), driven through `tanh`, times the kick function itself
- **clap / hat**: white noise through a band-pass / high-pass filter, times their rhythm functions
- **bass**: saw + sine through a low-pass filter
- **acid**: saw with a 303-style glide through a resonant state-variable (Chamberlin) filter, cutoff = `cutoff(x)`
- **sidechain**: bass and acid are multiplied by `1 − 0.75·kick(x)`, so they duck under the kick's own curve

## Using it in Cubase

**MIDI route: the math writes the notes, Cubase makes the sound.**

1. Set the project to the same tempo as `BPM` (140 by default).
2. Drag `out/song.mid` into the project, or use *File → Import → MIDI File…*. You get one track per part.
3. Kick, Clap and Hat are General MIDI drums on channel 10 (notes 36, 39, 42). Route them to Groove Agent SE or any drum sampler or synth.
4. Put Bass and Acid on Retrologue, or any mono synth with a resonant filter. For the acid line, make the filter resonant and give it a short filter envelope.
5. *Optional.* The Acid track also carries **CC74** with the cutoff curve. Most synths don't listen to it out of the box: map CC74 to the filter cutoff with the synth's MIDI learn or Cubase's Quick Controls, and the x² sweep opens the filter. Skip this step and the notes still play, just without the sweep. The acid stem below already has it.

**Audio route: the formulas are the sound.** Drag the WAVs onto audio tracks: ready-made ones are in `examples/stems/`, and your own renders go to `out/stems/`. They line up from bar 1 and add up to the mix (before its soft limiter). Process them like any other audio: EQ, reverb, more distortion.

Mix and match: formula kick and bass as audio, the acid line as MIDI into your favourite synth.

## Other DAWs

The same files work everywhere: Ableton Live, FL Studio, Logic, Bitwig, Reaper, Studio One. Import the MIDI or drag in the WAVs, then map CC74 to cutoff in the synth.

If you'd rather write formulas *inside* the DAW:

- **Surge XT** (free, VST3/AU/CLAP): its *Formula* modulator is a Lua script, so `mod`, `exp` and `sin` curves go straight to any parameter
- **Serum**: the wavetable editor has a formula parser for oscillator shapes
- **Cardinal** (free VCV Rack as a plugin): build the whole patch as modules inside your DAW
- **Bitwig Grid** and **Max for Live** (Ableton): modular environments where these curves are a few modules each

## Files

| file | what it is |
|---|---|
| `song.py` | the track: rhythm, pitch and modulation functions + arrangement. **Edit this one.** |
| `make_midi.py` | `song.py` → `out/song.mid` |
| `make_wav.py` | `song.py` → `out/mix.wav` + `out/stems/` |
| `beat.py` | helpers: `spike`, `mod`, scales, hit detection, MIDI and WAV writers |
| `examples/` | the default song, rendered: `song.mid`, `stems/*.wav`, `mix.mp3` |

MIT licensed: use it, break it, release tracks with it. If you make something, tag [@mathbeatlab](https://www.instagram.com/mathbeatlab).
