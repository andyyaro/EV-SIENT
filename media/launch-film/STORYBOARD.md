# EV-SIENT launch film

v2: 59 s, 1920×1080, rendered at 60 fps and blended to 30 fps (motion blur), HyperFrames 0.8.173.
Narration: Kokoro-82M, voice af_heart, with a studio chain. Music: "Retro Funk Energetic" by
Music_Unlimited (Pixabay Content License), about 116 BPM, so a bar is 2.07 s. Published 2026-10-23 at
https://futurecity.andyyaro.com/film.html. What this folder holds and what it leaves out: [README.md](README.md).

Everything on screen is real:

- the opening flies over the twelve candidate sites at night, drawn from OpenStreetMap data (`map/`);
- the laptop is a 3D model rendered frame by frame (`device/`), and the planner's window is held to its
  screen's four corners frame by frame until it lifts off;
- every screen is the live study site or planner, recorded frame by frame with the real pointer
  (`capture/`), then conformed to the narration (`tools/conform.py`).

## Build

```
tools/fetch_vendor.sh                                            # GSAP, three.js, MapLibre at their pinned versions
python3 -I map/build_sites.py                                    # the twelve sites, from site/redesign/www/data -> map/sites.json
python3 sound/voice.py --check                                   # narration (Kokoro-82M, af_heart) -> sound/vo/
python3 -I tools/build_cues.py                                   # cues.json -> assets/cues.js
python3 -I capture/takes.py app|site|assistant                   # record the live sites -> rec/, assets/rec/
python3 -I map/render.py                                         # the flight -> assets/map/hook.mp4 + hook.json
python3 -I device/render.py                                      # the laptop -> assets/device/laptop.mp4 + laptop.json
python3 -I tools/conform.py                                      # the edit -> assets/shots/*.mp4, assets/edit.js, clip times
python3 -I sound/events.py                                       # composition -> sound/events.json
python3 sound/design.py                                          # -> assets/audio/mix.wav (-16 LUFS)
python3 -I tools/captions.py                                     # -> deploy/film/ev-sient-launch.vtt
npx --yes hyperframes@0.8.173 check
npx --yes hyperframes@0.8.173 render -o renders/v2-raw60.mp4 --fps 60 --video-frame-format png --crf 10 --quiet
tools/finish.sh                                                  # blend to 30 fps, grade, grain, mux -> renders/ev-sient-launch-v2.mp4
deploy/publish.sh                                                # dry run; --apply publishes the watch page
```

The Python steps need Playwright (with Chromium), numpy and scipy; the narration also needs `kokoro`,
`soundfile` and `faster-whisper`. ffmpeg and Node are on the path.

`cues.json` is the one timing table for the narration; `tools/conform.py` holds the cut times. Every scene
is keyed to a narration word time, so moving a line moves its scene. Cuts inside the window snap to the
nearest beat (within 0.16 s).

## Music edit (film ← track, cut on downbeats)

| Film | Track | What the music does |
| --- | --- | --- |
| 0.00–17.67 | 0.00–17.67 | Quiet intro under the hook; the drop at 7.31 lands the logo |
| 17.67–48.73 | 50.81–81.87 | Breakdown under "how sure"; the second drop at 23.88 lands "Now it's your turn" |
| 48.73–59.00 | 94.30–end | End card on a downbeat; the song's own last accent at 56.50 (logo shine) |

## Beats

| Film (s) | Narration | Picture |
| --- | --- | --- |
| 0–2.9 | Every city wants more EV chargers. | A low glide over Fairfax City at night; the headline at the top |
| 2.9–5.0 | Few can show where the first ones should go, | The camera cranes up until the region is in view; the twelve sites switch on; the top three turn blue on "first" |
| 5.0–7.3 | and why. | Rank 1 rings on "why"; the camera dives onto Fairfax County Government Center |
| 7.3–9.4 | This is EV-SIENT. | The site's light becomes the Bolt Pin, planted on the building; the map goes dark; wordmark |
| 9.4–17.7 | We screened twelve public sites… safety and equity. | futurecity.andyyaro.com, recorded: push to the 12-site tile; the four weights fill on their words |
| 17.7–23.3 | Then we reweighted the model 2,000 times… | The Compare chart; 2,000 counter; push to Chance of First (70.8, 19.0, 10.2%) |
| 23.9–27.5 | Now it's your turn. Bring a spreadsheet… | Big type; a laptop rises into the light with the planner on its screen; example-city.csv dragged in and dropped |
| 27.5–34.2 | The planner matches your columns… never leaves your device. | The window lifts off the laptop; Accept All Matched; Run the Model and its real progress; "Your file stays on this device" |
| 34.2–42.0 | See every site ranked… in one click. | Ranked results; rank 1 chosen; Why This Score; Download .pdf clicked |
| 42.0–48.4 | Fill gaps with public data… even offline. | Window steps left; three notes; Look Up Public Data; a question typed to the assistant; Offline |
| 48.7–59.0 | EV-SIENT. Plan smarter charging… Try it free today. | Logo, line, address with Try it free, the study's address, disclaimer |

Every number on screen is one of the two sites' own. The planner screens use the invented Example City
sample and say so in the window's bar. Two moments are cut before their result on purpose: the public data
lookup (the hub does not cover Example City, which is invented) and the assistant's answer (see below).

## Sound

- Narration: high-pass 80 Hz, -2.5 dB at 280 Hz, +2.2 dB presence at 3.4 kHz, +2.5 dB air shelf, de-esser,
  3:1 compression, and a small synthetic room 15 dB under the voice.
- Ambience: a night city under the flight, louder near the ground and thinner as the camera climbs.
- Foley (Mixkit): the pointer's real clicks, real keystrokes for the typed question, the lights switching on,
  whooshes on the camera moves, the counter's ticks, panned to where they happen on screen.
- Master: two-pass loudnorm, -16 LUFS integrated, -1.5 dBTP.

## Notes for the planner

- The assistant re-take asked "What drives Site A's score?" with the one-site breakdown shared. The answer's
  first sentence came back, but every number after it read "(value not available)". The film cuts before the
  answer; the planner issue is worth a look.
- The Public Data lookup reports that the hub covers Virginia, New York, Maryland, the District of Columbia,
  Colorado and Illinois, so it finds nothing for Example City. The film cuts before the result.
- A CC BY-SA photo of the Government Center was considered for the dive and not used: the film shows the
  3D OpenStreetMap buildings instead, so no share-alike terms attach to the film.
