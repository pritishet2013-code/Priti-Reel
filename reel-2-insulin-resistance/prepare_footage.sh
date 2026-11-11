#!/usr/bin/env bash
# Builds project/assets/footage.mp4 from the untouched original:
#  - trims only silent gaps (no spoken words removed)
#  - voice loudness normalised to -14 LUFS for Instagram (no EQ/denoise, tone unchanged)
#  - G1 warm-natural grade, 576x1024 -> 1080x1920 lanczos upscale + light sharpen
set -euo pipefail
cd "$(dirname "$0")"
IN=source/Priti_Reel_2_original.mp4
OUT=project/assets/footage.mp4
# keep segments (source seconds) — gaps removed: 0.00-0.18, 4.47-4.72, 6.05-6.32, 12.15-12.51
SEGS=("0.18 4.47" "4.72 6.05" "6.32 12.15" "12.51 20.167")
GRADE="scale=1080:1920:flags=lanczos,unsharp=5:5:0.35,colorbalance=rs=0.015:gs=0.005:bs=-0.025:rm=0.01:bm=-0.015:rh=0.01:bh=-0.01,eq=contrast=1.03:brightness=0.012:saturation=0.96:gamma=1.01"
fc=""; cat=""
for i in "${!SEGS[@]}"; do
  read -r a b <<<"${SEGS[$i]}"
  d=$(python3 -c "print(round($b-$a,3))"); fo=$(python3 -c "print(round($b-$a-0.012,3))")
  fc+="[0:v]trim=$a:$b,setpts=PTS-STARTPTS[v$i];"
  fc+="[0:a]atrim=$a:$b,asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st=$fo:d=0.012[a$i];"
  cat+="[v$i][a$i]"
done
fc+="${cat}concat=n=${#SEGS[@]}:v=1:a=1[vc][ac];[ac]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout];[vc]$GRADE,format=yuv420p[vo]"
ffmpeg -v error -y -i "$IN" -filter_complex "$fc" -map "[vo]" -map "[aout]" \
  -c:v libx264 -preset slow -crf 16 -r 30 -c:a aac -b:a 192k -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
