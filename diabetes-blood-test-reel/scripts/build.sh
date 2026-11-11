#!/usr/bin/env bash
# Builds output/PCOS_Blood_Tests_Reel.mp4 (1080x1920, 30 fps, H.264 + AAC).
#   1. render the GSAP overlay to a transparent PNG sequence
#   2. synthesise the music bed + pop SFX
#   3. composite over the presenter video (gentle slow zoom), clean + mix audio;
#      the last frame is held under the opaque closing CTA screen
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HERE/source/Raw_Video_2.mp4"
WORK="${WORK:-$HERE/.work}"
OUT="$HERE/output/Diabetes_Blood_Tests_Reel.mp4"
MAIN=16.95   # presenter footage
DUR=23.0     # + closing CTA screen
mkdir -p "$WORK/frames" "$HERE/output"

node "$HERE/scripts/render-overlay.mjs" "$WORK/frames"
python3 "$HERE/scripts/make_audio_beds.py" "$WORK" "$DUR" "$WORK/frames/sfx.json"

# Audio: voice high-pass + FFT denoise + gentle compression + loudness normalise;
# music at ~9% of the voice level; pops very quiet.
# 3a. audio mix -> WAV (kept as its own pass so the padded tail under the CTA stays intact)
ffmpeg -y -v error -i "$SRC" -i "$WORK/music.wav" -i "$WORK/sfx.wav" \
  -filter_complex "
    [0:a]atrim=0:${MAIN},highpass=f=85,afftdn=nr=14:nf=-38:tn=1,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,
         loudnorm=I=-15:TP=-1.5:LRA=9,aresample=48000,apad=whole_dur=${DUR}[voice];
    [1:a]volume=0.125[music];
    [2:a]volume=0.06[sfx];
    [voice][music][sfx]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:${DUR},asetpts=N/SR/TB[a]" \
  -map "[a]" -c:a pcm_s16le "$WORK/mix.wav"

# 3b. background: presenter video, 30 fps, slow push-in, last frame held under the CTA.
#     Rendered to a near-lossless intermediate (overlay would otherwise stop at the source's EOF).
ffmpeg -y -v warning -stats -i "$SRC" \
  -vf "trim=0:${MAIN},setpts=PTS-STARTPTS,fps=30,tpad=stop_mode=clone:stop_duration=$(echo "$DUR - $MAIN + 0.1" | bc),
       scale=1080:1937:flags=lanczos,crop=1080:1920:0:8,setsar=1,
       scale=w='trunc(1080*(1+0.04*min(t,${MAIN})/${MAIN})/2)*2':h='trunc(1920*(1+0.04*min(t,${MAIN})/${MAIN})/2)*2':eval=frame:flags=lanczos,
       crop=1080:1920:'(iw-1080)/2':'(ih-1920)*0.45',format=yuv420p" \
  -an -t "$DUR" -c:v libx264 -preset fast -crf 8 "$WORK/bg.mp4"

# 3c. overlay + mux
ffmpeg -y -v warning -stats \
  -i "$WORK/bg.mp4" \
  -framerate 30 -i "$WORK/frames/f_%05d.png" \
  -i "$WORK/mix.wav" \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]" \
  -map "[v]" -map 2:a -t "$DUR" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"

echo "Done: $OUT"
