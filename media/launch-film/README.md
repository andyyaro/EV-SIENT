# EV-SIENT launch film

The 59-second film at the top of the [repository README](../../README.md), published at
https://futurecity.andyyaro.com/film.html. It shows the study site (futurecity.andyyaro.com) and the
planner (app.futurecity.andyyaro.com), and every screen in it is one of the two live sites, recorded
frame by frame. The planner shots use Example City, the invented sample in
`platform/app/public/samples/`.

[STORYBOARD.md](STORYBOARD.md) has the beats, the music edit, the sound design and every build step.

## What is here

| Path | What it is |
|---|---|
| `index.html` | The composition (HyperFrames 0.8.173, GSAP): every scene, keyed to the narration's word times |
| `cues.json`, `tools/build_cues.py` | The one timing table for picture, pointer and sound |
| `capture/` | Playwright recordings of the live sites (`takes.py`) and the stills (`stills.py`) |
| `map/` | The opening flight over the twelve sites: `flight.html` (MapLibre, OpenFreeMap tiles), `render.py`, `build_sites.py` |
| `device/` | The procedural 3D laptop (`laptop.html`, three.js) and its renderer |
| `tools/conform.py` | The edit: which recorded frame plays on each film frame |
| `sound/` | Narration (`voice.py`, Kokoro-82M voice af_heart), the music beat grid, the mix (`design.py`) |
| `tools/captions.py`, `tools/finish.sh` | The captions file; motion blur, grade, grain and the final encode |
| `deploy/film.html`, `deploy/publish.sh` | The watch page and the script that publishes it |
| `assets/brand/` | The EV-SIENT logo files the film uses |
| `assets/audio/SOURCE.md` | Where every sound and picture source came from, with its licence |

## What is not here, and why

The working folder for the film is about 1.8 GB. This folder keeps the source and leaves out
everything that is generated or that its licence does not let us redistribute on its own:

- **Generated:** the screen recordings (`rec/`), the conformed shots, the map and laptop renders,
  the narration audio, the mix, the renders and the published MP4. The build steps make them again.
- **Third-party media:** the music ("Retro Funk Energetic" by Music_Unlimited, Pixabay Content
  License) and the 24 Mixkit sound effects (Mixkit Sound Effects Free License). Both licences allow
  them inside a film and not as files handed on by themselves. `assets/audio/SOURCE.md` lists each
  one with its id so it can be downloaded again into `assets/audio/`.
- **Libraries and fonts:** GSAP 3.14.2, three.js 0.186.0 and MapLibre GL JS 6.12.0 are fetched at
  their pinned versions by `tools/fetch_vendor.sh`. The Inter and Inter Display web fonts (SIL OFL
  1.1) go in `assets/fonts/` from the Inter 4 release.
- **Site data:** `map/sites.json` is built from the public site's own data by `map/build_sites.py`,
  so the film's ranks always match futurecity.andyyaro.com.

## Publishing

`deploy/publish.sh` copies the watch page, the MP4, its poster, the logo and the captions file to
the redesigned site's bucket, and invalidates `/film.html` and `/film/*`. It is a dry run unless
given `--apply`. `site/redesign/tools/deploy.sh` excludes `film.html` and `film/`, so a deploy of
the site never deletes the film.

## Credits

Narration: Kokoro-82M (Apache-2.0), voice af_heart. Music: "Retro Funk Energetic" by Music_Unlimited
(Pixabay). Sound effects: Mixkit. Map data © OpenStreetMap contributors, © OpenMapTiles; tiles by
OpenFreeMap, drawn with MapLibre GL JS. The laptop is drawn with three.js.
