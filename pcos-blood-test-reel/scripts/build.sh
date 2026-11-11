#!/usr/bin/env bash
# Builds output/PCOS_Blood_Tests_Reel.mp4 (1080x1920, 30 fps, H.264 + AAC).
#   1. render the GSAP overlay to a transparent PNG sequence
#   2. synthesise the music bed + pop SFX
#   3. composite over the presenter video (gentle slow zoom), clean + mix audio
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HERE/source/Raw_Video_2.mp4"
WORK="${WORK:-$HERE/.work}"
OUT="$HERE/output/PCOS_Blood_Tests_Reel.mp4"
DUR=16.95
mkdir -p "$WORK/frames" "$HERE/output"

node "$HERE/scripts/render-overlay.mjs" "$WORK/frames"
python3 "$HERE/scripts/make_audio_beds.py" "$WORK" "$DUR" "$WORK/frames/sfx.json"

# Video: 60fps 464x832 -> 30fps 1080x1920, slow 0 -> 4% push-in (centred a little high
# so the face stays clear of the overlay), overlay on top.
# Audio: voice high-pass + FFT denoise + gentle compression + loudness normalise;
# music at ~9% of the voice level; pops very quiet.
ffmpeg -y -v warning -stats \
  -i "$SRC" \
  -framerate 30 -i "$WORK/frames/f_%05d.png" \
  -i "$WORK/music.wav" -i "$WORK/sfx.wav" \
  -filter_complex "
    [0:v]fps=30,scale=1080:1937:flags=lanczos,crop=1080:1920:0:8,setsar=1,
         scale=w='trunc(1080*(1+0.04*t/${DUR})/2)*2':h='trunc(1920*(1+0.04*t/${DUR})/2)*2':eval=frame:flags=lanczos,
         crop=1080:1920:'(iw-1080)/2':'(ih-1920)*0.45',format=yuv420p[bg];
    [bg][1:v]overlay=0:0:format=auto,format=yuv420p[v];
    [0:a]highpass=f=85,afftdn=nr=14:nf=-38:tn=1,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,
         loudnorm=I=-15:TP=-1.5:LRA=9,aresample=48000[voice];
    [2:a]volume=0.125[music];
    [3:a]volume=0.06[sfx];
    [voice][music][sfx]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95,atrim=0:${DUR}[a]" \
  -map "[v]" -map "[a]" -t "$DUR" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"

echo "Done: $OUT"
