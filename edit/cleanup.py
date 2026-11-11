"""Repair pass for an existing build/clean.mkv: paint stray matte islands back to background.

enhance.py now removes islands itself; this lets an older clean.mkv be fixed without
re-running the 45-minute upscale. It recomputes the matte (fast), finds what
keep_main_body() would drop, and blends those pixels to the brand background.
"""
import os, subprocess
import numpy as np
import onnxruntime as ort
import cv2
from PIL import Image
import enhance as E

def main():
    so = ort.SessionOptions(); so.intra_op_num_threads = 4
    P = ["CPUExecutionProvider"]
    mod = ort.InferenceSession(os.path.join(E.MODELS, "modnet.onnx"), so, providers=P)
    seg = ort.InferenceSession(os.path.join(E.MODELS, "selfie_mc.onnx"), so, providers=P)
    bg = E.background()
    src = subprocess.Popen(["ffmpeg", "-v", "error", "-i", os.path.join(E.BUILD, "cut_native.mkv"),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    cln = subprocess.Popen(["ffmpeg", "-v", "error", "-i", os.path.join(E.BUILD, "clean.mkv"),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    tmp = os.path.join(E.BUILD, "clean_fixed.mkv")
    out = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{E.W}x{E.H}", "-r", "30", "-i", "-",
                            "-c:v", "libx264", "-crf", "8", "-preset", "medium", "-pix_fmt", "yuv444p", tmp],
                           stdin=subprocess.PIPE)
    keep_main_body = E.keep_main_body
    prev, n, fixed = None, 0, 0
    while True:
        b1 = src.stdout.read(E.SW * E.SH * 3); b2 = cln.stdout.read(E.W * E.H * 3)
        if len(b1) < E.SW * E.SH * 3 or len(b2) < E.W * E.H * 3: break
        im = Image.frombuffer("RGB", (E.SW, E.SH), b1)
        E.keep_main_body = lambda a: a                       # raw matte, as originally used
        raw = E.matte(im, mod, seg, prev)
        E.keep_main_body = keep_main_body
        kept = keep_main_body(raw)
        prev = raw
        drop = np.clip((raw - kept) / np.maximum(raw, 1e-3), 0, 1) * (raw > 0.02)
        drop = cv2.GaussianBlur(drop.astype(np.float32), (0, 0), 3)[..., None]
        frame = np.frombuffer(b2, np.uint8).reshape(E.H, E.W, 3).astype(np.float32)
        if drop.max() > 0.05: fixed += 1
        frame = frame * (1 - drop) + bg * drop
        out.stdin.write(frame.clip(0, 255).astype(np.uint8).tobytes())
        n += 1
    out.stdin.close(); out.wait()
    os.replace(tmp, os.path.join(E.BUILD, "clean.mkv"))
    print("frames", n, "repaired", fixed)

if __name__ == "__main__":
    main()
