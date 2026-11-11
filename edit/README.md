# Insulin Resistance reel — edit pipeline

Final reel: `output/Priti_Insulin_Resistance_Reel.mp4` (1080x1920, 30 fps, ~17.2 s).

Rebuild (Python 3, ffmpeg; `pip install onnxruntime opencv-python-headless<5 noisereduce faster-whisper huggingface_hub pillow numpy`):
1. `python3 edit/cut.py` — voice enhancement (noise print from room tone, spectral noise
   reduction, EQ, de-ess, compression, -14 LUFS), silence cut (never words), warm grade (G1).
2. Transcribe `edit/build/voice.wav` to `edit/build/words.json` (faster-whisper medium, word timestamps).
3. `python3 edit/enhance.py` — Real-ESRGAN 4x upscale to 1080x1920 and background removal
   (MODNet edges gated by a MediaPipe person mask) onto the brand mint background. ~45 min on 4 CPUs.
   (`python3 edit/cleanup.py` repairs an older clean.mkv by removing stray matte islands; not needed after a fresh enhance.py run.)
4. `python3 edit/render.py` — graphics, punch-ins, generated SFX, final encode.
   `python3 edit/render.py --preview 0.3,8.2` writes stills to `edit/build/preview/`.

Models (downloaded from the Hugging Face Hub on first run):
Real-ESRGAN general-x4v3 (BSD-3), MODNet (Apache-2.0), MediaPipe selfie multiclass (Apache-2.0).

Styles: H1 headline, C2 captions, B3 tick list, B6 "2+" turn word,
E1 save card + end card ("Follow for more simple health tips"), M1 punch-ins, S1 light ticks, G1 grade.
Removed on request: logo, B1 step tracker. L1 (demo above) skipped: no screen recording;
symptom images pop above the pointing finger instead.

Brand: background mint #BCE4B5 (Colour.png); accents use the logo gradient #55BE38 -> #4A96B4.
Symptom photos in `edit/assets/` are cropped from Reference video 1 (as requested) and upscaled.
Font: Caveat (SIL OFL) in `edit/fonts/`; Inter Display from the system.
