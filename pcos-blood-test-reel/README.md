# PCOS Edition – Symptoms vs Blood Tests (Instagram Reel)

Final video: `output/PCOS_Blood_Tests_Reel.mp4` (1080×1920, 9:16, 30 fps, H.264/AAC, ~17 s).

Modelled on `../Reference for blood test reel.mp4`: a heading at the top, two column labels, a dotted
divider, and each symptom on the left with its blood tests on the right. Branded with the
Priti's Diet Clinic palette: cream `#FFF8EE`, sage `#BDE5B5`, blush `#F7C8D4` and a hot blush-pink
heading `#D93D7A`.

## Timing (matched to the presenter's pointing gestures)
| Step | Symptom (left hand up) | Tests (right hand up) |
|---|---|---|
| 1 Irregular or missed periods | 0.80 s | 2.30 s |
| 2 Jawline acne, facial hair | 4.55 s | 6.50 s |
| 3 Hair thinning | 8.55 s | 10.75 s |
| 4 Constant fatigue, joint pain, inflammation | 12.75 s | 14.70 s |

## Files
- `source/Raw_Video_2.mp4`: an untouched copy of the original raw video.
- `composition/index.html`: the GSAP overlay. Open `composition/index.html?preview=1` to watch it over the video.
- `scripts/render-overlay.mjs`: renders the overlay to transparent PNG frames using Playwright.
- `scripts/make_audio_beds.py`: generates the background music and the soft "pop" sound effects.
- `scripts/build.sh`: composites the video with a slow 4 % zoom, cleans the voice
  (high-pass filter, noise reduction, compression and loudness normalisation to −15 LUFS), mixes in
  music at about 9 % and exports the MP4.

To rebuild after editing text or timings in `index.html`: `scripts/build.sh` (needs node, Playwright, python3 + numpy and ffmpeg).
