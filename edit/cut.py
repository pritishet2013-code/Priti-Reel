"""Step 1: cut silences (never words), scale to 1080x1920, warm grade (G1), clean voice.

Speech spans come from ffmpeg silencedetect at -30 dB on the raw clip. Each span is
padded so word onsets/tails are never clipped, and pauses collapse to a short breath.
Writes build/cut.mov and build/timeline.json (source->output time map).
"""
import json, subprocess, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "Priti_video_raw.mp4")
BUILD = os.path.join(HERE, "build")
os.makedirs(BUILD, exist_ok=True)

# Speech spans (seconds, source time) measured with silencedetect noise=-30dB d=0.3.
SPANS = [
    (0.264, 1.325),   # Insulin resistance (1)
    (1.730, 2.810),   # (2)
    (3.245, 4.345),   # (3)
    (4.804, 5.866),   # (4)
    (6.407, 7.462),   # (5)
    (7.886, 10.028),  # If you have more than two of these symptoms,
    (10.294, 12.013), # then you can be insulin resistant.
    (12.335, 14.536), # If you want to know more about this,
    (15.047, 18.381), # read my caption and kindly follow me for more science
    (18.763, 19.396), # backed options.
]
PRE, POST = 0.07, 0.09          # padding around speech
SENTENCE_BREAKS = {4, 6, 7}     # after these span indexes keep a slightly longer breath
BREATH_EXTRA = 0.06

def main():
    keep = []
    for i, (s, e) in enumerate(SPANS):
        a = max(0.0, s - PRE)
        b = e + POST + (BREATH_EXTRA if i in SENTENCE_BREAKS else 0)
        if i + 1 < len(SPANS):
            b = min(b, SPANS[i + 1][0] - PRE)
        keep.append((round(a, 3), round(b, 3)))

    out_t, segs = 0.0, []
    for a, b in keep:
        segs.append({"src_start": a, "src_end": b, "out_start": round(out_t, 3)})
        out_t += b - a
    json.dump({"segments": segs, "duration": round(out_t, 3)},
              open(os.path.join(BUILD, "timeline.json"), "w"), indent=1)

    # Build filtergraph: trim each piece, 8 ms audio fades to avoid clicks, concat.
    parts, labels = [], []
    for i, (a, b) in enumerate(keep):
        d = b - a
        parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.008,afade=t=out:st={d-0.008:.3f}:d=0.008[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    n = len(keep)
    grade = (  # G1 Warm Natural: gentle warmth in mids/highs, protect skin + red kurta
        "scale=1080:1920:flags=lanczos,unsharp=5:5:0.35,"
        "colorbalance=rm=0.025:gm=0.008:bm=-0.03:rh=0.015:bh=-0.02,"
        "eq=contrast=1.03:brightness=0.012:saturation=0.98,format=yuv420p"
    )
    parts.append("".join(labels) + f"concat=n={n}:v=1:a=1[vc][ac]")
    parts.append(f"[vc]{grade}[vout]")
    parts.append("[ac]highpass=f=80,afftdn=nf=-30,"
                 "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,"
                 "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[aout]")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", ";".join(parts),
           "-map", "[vout]", "-map", "[aout]", "-r", "30",
           "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-c:a", "pcm_s16le",
           os.path.join(BUILD, "cut.mov")]
    subprocess.run(cmd, check=True)
    print("output duration", round(out_t, 3))

if __name__ == "__main__":
    main()
