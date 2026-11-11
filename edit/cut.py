"""Step 1: voice enhancement + silence cut (never words) + warm grade (G1), at native res.

Voice: spectral noise reduction using a noise print taken from the room-tone gaps,
then EQ (rumble cut, de-mud, presence, air), de-ess, gentle compression, -14 LUFS.
Speech spans come from ffmpeg silencedetect at -30 dB on the raw clip; each span is
padded so word onsets/tails are never clipped, and pauses collapse to a short breath.
Writes build/cut_native.mkv (graded video, native 576x1024), build/voice.wav and
build/timeline.json (source->output time map).
"""
import json, subprocess, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "Priti_video_raw.mp4")
BUILD = os.path.join(HERE, "build")
os.makedirs(BUILD, exist_ok=True)
SR = 48000

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
NOISE_PRINT = [(14.62, 14.98), (19.50, 20.10)]   # room tone only
PRE, POST = 0.07, 0.09
SENTENCE_BREAKS = {4, 6, 7}
BREATH_EXTRA = 0.06

def run(cmd): subprocess.run(cmd, check=True)

def enhance_voice():
    raw = os.path.join(BUILD, "raw48k.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-ac", "1", "-ar", str(SR), raw])
    w = wave.open(raw); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    import noisereduce as nr
    noise = np.concatenate([x[int(a * SR):int(b * SR)] for a, b in NOISE_PRINT])
    y = nr.reduce_noise(y=x, sr=SR, y_noise=noise, stationary=True, prop_decrease=0.85,
                        n_fft=2048, freq_mask_smooth_hz=300, time_mask_smooth_ms=60)
    # second, gentler non-stationary pass for anything that moves (AC, street)
    y = nr.reduce_noise(y=y, sr=SR, stationary=False, prop_decrease=0.5, n_fft=2048)
    dn = os.path.join(BUILD, "denoised.wav")
    with wave.open(dn, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
        o.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    return dn

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

    dn = enhance_voice()
    parts, labels = [], []
    for i, (a, b) in enumerate(keep):
        d = b - a
        parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[1:a]atrim={a}:{b},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.008,afade=t=out:st={d-0.008:.3f}:d=0.008[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    n = len(keep)
    grade = (  # G1 Warm Natural: gentle warmth, protect skin + red kurta
        "colorbalance=rm=0.025:gm=0.008:bm=-0.03:rh=0.015:bh=-0.02,"
        "eq=contrast=1.03:brightness=0.012:saturation=0.98"
    )
    voice = (  # rumble cut, de-mud, presence, air, de-ess, compress, loudness
        "highpass=f=85,lowpass=f=15000,"
        "equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3500:t=q:w=1.0:g=3,"
        "highshelf=f=10000:g=1.5,deesser=i=0.35,"
        "acompressor=threshold=-22dB:ratio=3:attack=6:release=110:makeup=2,"
        "loudnorm=I=-14:TP=-1.5:LRA=8,aresample=48000"
    )
    parts.append("".join(labels) + f"concat=n={n}:v=1:a=1[vc][ac]")
    parts.append(f"[vc]{grade}[vout]")
    parts.append(f"[ac]{voice}[aout]")
    run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-i", dn, "-filter_complex", ";".join(parts),
         "-map", "[vout]", "-map", "[aout]", "-r", "30",
         "-c:v", "ffv1", "-c:a", "pcm_s16le", os.path.join(BUILD, "cut_native.mkv")])
    run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(BUILD, "cut_native.mkv"), "-vn",
         "-c:a", "pcm_s16le", os.path.join(BUILD, "voice.wav")])
    print("output duration", round(out_t, 3))

if __name__ == "__main__":
    main()
