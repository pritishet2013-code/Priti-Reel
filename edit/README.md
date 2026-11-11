# Insulin Resistance reel — edit pipeline

Final reel: `output/Priti_Insulin_Resistance_Reel.mp4` (1080x1920, 30 fps, ~17.2 s).

Rebuild:
1. `python3 edit/cut.py` — cuts silences (never words), scales to 1080x1920, warm grade (G1), cleans voice.
2. Transcribe `edit/build/cut.mov` to `edit/build/words.json` (faster-whisper medium, word timestamps).
3. `python3 edit/render.py` — graphics, punch-ins, generated SFX, final encode.
   `python3 edit/render.py --preview 0.0,5.6,8.2` writes stills to `edit/build/preview/`.

Styles: H1 headline, C2 captions, B1 step tracker, B3 tick list, B6 "2+" turn word,
E1 save card + end card ("Follow for more simple health tips"), M1 punch-ins, S1 light ticks, G1 grade.
L1 (demo above) skipped: no screen recording; symptom images pop above the pointing finger instead.

Brand: mint #BCE4B5 (Colour.png), logo gradient #55BE38 -> #4A96B4 (Logo.png).
Symptom photos in `edit/assets/` are cropped from Reference video 1 (as requested).
Font: Caveat (SIL OFL) in `edit/fonts/`; Inter Display from the system.
