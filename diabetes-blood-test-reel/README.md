# Diabetes Edition – 7 Warning Signs (Instagram Reel)

Final video: `output/Diabetes_Blood_Tests_Reel.mp4` (1080×1920, 9:16, 30 fps, H.264/AAC, 23 s:
17 s of presenter footage, then a 6 s closing call-to-action screen).

This uses the same editing pattern as `../pcos-blood-test-reel` (the PCOS Edition reel): the same presenter
clip, the same timings matched to the pointing gestures, and the same layout and animations.
Colours: pink `#E83E78`, white `#FFFFFF`, dark text `#222222`, cream `#FFF7EF`, sage `#DDEBD5`.

## Scenes
| Scene | Symptom (left hand up) | Blood tests (right hand up) |
|---|---|---|
| 1 | Excessive thirst & frequent urination (0.80 s) | HbA1c, Fasting Blood Glucose, Random Blood Glucose (2.30 s) |
| 2 | Slow-healing wounds (4.55 s) | HbA1c, Fasting Blood Glucose, Random Blood Glucose (6.50 s) |
| 3 | Tingling or numbness in feet (8.55 s) | HbA1c, Fasting Blood Glucose, Vitamin B12 (when clinically indicated) (10.75 s) |
| 4 | Unexplained weight loss & increased hunger (12.75 s) | HbA1c, Fasting Blood Glucose, Random Blood Glucose (14.70 s) |

In every scene, HbA1c gets a soft sage highlight with a pink edge.

## Closing screen (16.95 s to 23 s)
1. **SAVE THIS REEL** (animated bookmark)
2. **FOLLOW @PRITISDIETCLINIC**
3. **Share this with someone who needs to check their blood sugar.**

## Images
`composition/images/` holds the four symptom images, generated with Canva for this reel. To use your own
photos instead, replace a file with one of the same name and run the build again.

## Rebuild
`scripts/build.sh` (needs node, Playwright, python3 + numpy and ffmpeg). See `../pcos-blood-test-reel/README.md`
for details of the pipeline.
