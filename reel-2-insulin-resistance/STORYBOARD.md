# Priti Reel 2 – "4 Signs of Insulin Resistance" – Storyboard v2

Status: **draft preview built (`export/PREVIEW_draft_not_final.mp4`). Final MP4 waits for Priti's approval.**

## Folder layout
- `source/` – untouched original video and the original GitHub symptom images
- `prepare_footage.sh` – trims silent gaps only, voice loudness → −14 LUFS, G1 grade, 576×1024 → 1080×1920 upscale
- `make_sfx.py` – synthesises the soft pop / tick / whoosh / paper sounds (no licensing issues)
- `project/` – editable HyperFrames project (`index.html` = composition; HTML/CSS/GSAP)
- `export/` – rendered videos

## Source
- 20.17 s, portrait 576×1024, 30 fps. Exact speech (verified with two Whisper models):
  1. "Insulin resistance" ×5 – pointing right, left, right, left in turns
  2. "If you have more than two of these symptoms, then you can be insulin resistant."
  3. "If you want to know more about this, read my caption and kindly follow me for more science-backed options."
- Silent gaps removed (no words cut): 0.00–0.18, 4.47–4.72, 6.05–6.32, 12.15–12.51 → **final 19.1 s**

## Timeline (edited seconds)
| Time | Speech | Styles | On screen |
|---|---|---|---|
| 0.00–1.48 | "Insulin resistance" (hook) | H1, M1 | Full headline from frame 1 on chest: "4 SIGNS OF" white / "INSULIN RESISTANCE" black on yellow bar. Punch-in 100→105 %. Logo badge top-left. Headline pulses on each "insulin resistance". |
| 1.48–3.00 | "Insulin resistance" (points right) | Pointing image, S1 pop | ① Dark Neck card, top-right |
| 3.00–4.29 | "Insulin resistance" (points left) | Pointing image | ② Skin Tags card, top-left above her raised finger |
| 4.29–5.62 | "Insulin resistance" (points right) | Pointing image, M1 cut | ③ Belly Fat card, top-right |
| 5.62–7.04 | "Insulin resistance" (points left) | Pointing image, M1 cut | ④ Sugar Cravings card, top-left |
| 7.05–11.20 | "If you have more than two of these symptoms…" | B3, B6, C2, captions | "CHECK YOUR SIGNS" cream checklist (top-right) ticks 1-2-3-4. B6: big yellow **TWO**. C2: small "THEN YOU CAN BE" + big yellow "INSULIN RESISTANT." |
| 11.45 | – | M1 | Jump cut hidden by scale change |
| 11.50–13.82 | "If you want to know more about this," | captions | – |
| 13.84–15.00 | "read my caption" | B6, paper card | Big yellow **READ**; "READ THE CAPTION ↓" paper card replaces headline |
| 15.12–19.10 | "and kindly follow me for more science-backed options." | E1, CTA, B6 | SAVE THIS REEL paper card with animated bookmark → "FOLLOW @PRITISDIETCLINIC" (15.74) → "Share with someone who needs this" (16.74). Big yellow **FOLLOW**. |
| 17.05–19.10 | (end) | Branding | Logo + PRITI'S DIET CLINIC + @pritisdietclinic card above her head. She stays on screen; no black frames. |

## Look and sound
- Brand: sage #BDE4B5, leaf #55BF38 → teal #4A96B5, cream #FAF6EE, yellow #FFE135 (keywords only). Montserrat 700–900 + Poppins 500–700.
- G1: slight warmth (colorbalance), +3 % contrast, −4 % saturation so the red outfit doesn't glow, light lanczos sharpen. No smoothing or filters.
- S1: pops on symptom cards, ticks on checklist, whoosh on C2/READ/end card, paper swish on Save card. Measured mix: voice −13.7 LUFS, peaks −1.4 dBFS; effects add 0 dB to voice peaks.
- Music: none (only licensed tracks Priti supplies).

## Safe zones
All text and cards sit between y ≈ 196 and y ≈ 1548 (1080×1920), inside the Reels/TikTok UI-free area. No overlay covers the face (≈ x 400–780, y 580–1120).

## To render the final after approval
```
cd project && npx hyperframes check && npx hyperframes render -q delivery -o ../export/Pritis_Insulin_Resistance_Reel.mp4
```
