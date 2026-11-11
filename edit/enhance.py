"""Step 2: upscale + background removal -> build/clean.mkv (1080x1920, brand background).

Upscale: Real-ESRGAN general-x4v3 (BSD-3) 4x, blended with a Lanczos upscale so skin
keeps natural texture instead of a painted look.
Matte: MODNet (Apache-2.0) gives the soft hair edge; MediaPipe selfie multiclass
(Apache-2.0) gives a person-only mask that gates out the chair and wall.
Alpha is smoothed over time to stop edge flicker. Background: brand mint #BCE4B5
with a soft lighter centre.
Models are fetched from the Hugging Face Hub into build/models/.
"""
import os, subprocess, shutil
import numpy as np
import onnxruntime as ort
import cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
MODELS = os.path.join(BUILD, "models")
W, H, SW, SH = 1080, 1920, 576, 1024
ESRGAN_MIX = 0.65          # share of the AI upscale in the final pixels
MINT = np.array([188, 228, 181], np.float32)
MINT_LIGHT = np.array([214, 240, 208], np.float32)

def fetch():
    from huggingface_hub import hf_hub_download
    os.makedirs(MODELS, exist_ok=True)
    for repo, f, dst in [("Heliosoph/realesrgan-onnx", "realesr-general-x4v3.onnx", "esrgan.onnx"),
                         ("Xenova/modnet", "onnx/model.onnx", "modnet.onnx"),
                         ("senty-au/selfie_multiclass_256x256-ONNX", "onnx/model.onnx", "selfie_mc.onnx")]:
        p = os.path.join(MODELS, dst)
        if not os.path.exists(p): shutil.copy(hf_hub_download(repo, f), p)

def background():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W * 0.5) / (W * 0.75)) ** 2 + ((yy - H * 0.42) / (H * 0.6)) ** 2)
    k = np.clip(1 - d, 0, 1)[..., None] ** 1.5
    return MINT * (1 - k) + MINT_LIGHT * k

def keep_main_body(a):
    """Drop stray islands (chair bits, specks): keep the body and any big connected part."""
    hard = (a > 0.3).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(hard, connectivity=8)
    if n <= 2: return a
    areas = stats[1:, cv2.CC_STAT_AREA]
    big = areas.max()
    keep = np.isin(lab, 1 + np.where(areas >= 0.05 * big)[0]).astype(np.uint8)
    keep = cv2.dilate(keep, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    keep = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 4)
    return a * keep

def matte(im, mod, seg, prev_a):
    m_in = np.asarray(im.resize((512, 896), Image.BILINEAR), np.float32).transpose(2, 0, 1)[None] / 127.5 - 1
    a_mod = mod.run(None, {"input": m_in})[0][0, 0]
    s_in = (np.asarray(im.resize((256, 256), Image.BILINEAR), np.float32) / 255)[None]
    logits = seg.run(None, {seg.get_inputs()[0].name: s_in})[0][0]
    e = np.exp(logits - logits.max(-1, keepdims=True)); prob = e / e.sum(-1, keepdims=True)
    person = 1 - prob[..., 0]
    a_mod = cv2.resize(a_mod, (W, H), interpolation=cv2.INTER_CUBIC)
    a_mod = np.clip((a_mod - 0.12) / 0.78, 0, 1)          # kill faint background residue
    p = cv2.resize(person.astype(np.float32), (SW, SH), interpolation=cv2.INTER_LINEAR)
    hard = (p > 0.5).astype(np.uint8)
    gate = cv2.dilate(hard, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
    gate = cv2.GaussianBlur(gate.astype(np.float32), (0, 0), 3)
    core = cv2.erode(hard, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))).astype(np.float32)
    core = cv2.GaussianBlur(core, (0, 0), 2)
    gate = cv2.resize(gate, (W, H), interpolation=cv2.INTER_LINEAR)
    core = cv2.resize(core, (W, H), interpolation=cv2.INTER_LINEAR)
    a = np.maximum(a_mod * gate, core)                     # fill holes inside the body
    if prev_a is not None:                                  # temporal smoothing
        a = 0.7 * a + 0.3 * prev_a
    return keep_main_body(a)


def main():
    fetch()
    so = ort.SessionOptions(); so.intra_op_num_threads = 4
    P = ["CPUExecutionProvider"]
    esr = ort.InferenceSession(os.path.join(MODELS, "esrgan.onnx"), so, providers=P)
    mod = ort.InferenceSession(os.path.join(MODELS, "modnet.onnx"), so, providers=P)
    seg = ort.InferenceSession(os.path.join(MODELS, "selfie_mc.onnx"), so, providers=P)
    bg = background()

    src = subprocess.Popen(["ffmpeg", "-v", "error", "-i", os.path.join(BUILD, "cut_native.mkv"),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    out = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                            "-c:v", "libx264", "-crf", "8", "-preset", "medium", "-pix_fmt", "yuv444p",
                            os.path.join(BUILD, "clean.mkv")], stdin=subprocess.PIPE)
    prev_a, n = None, 0
    limit = int(os.environ.get("MAX_FRAMES", "0"))
    while True:
        buf = src.stdout.read(SW * SH * 3)
        if len(buf) < SW * SH * 3: break
        im = Image.frombuffer("RGB", (SW, SH), buf)
        x = np.asarray(im, np.float32)

        # --- upscale
        t = (x / 255).transpose(2, 0, 1)[None]
        y = esr.run(None, {"input": t})[0][0].transpose(1, 2, 0).clip(0, 1) * 255
        ai = np.asarray(Image.fromarray(y.astype(np.uint8)).resize((W, H), Image.LANCZOS), np.float32)
        lz = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32)
        fg = ai * ESRGAN_MIX + lz * (1 - ESRGAN_MIX)

        # --- matte
        a = matte(im, mod, seg, prev_a)
        prev_a = a

        # light wrap: tint the outer edge a touch toward the background
        edge = (a * (1 - a) * 4)[..., None] * 0.25
        fgw = fg * (1 - edge) + bg * edge
        comp = fgw * a[..., None] + bg * (1 - a[..., None])
        out.stdin.write(comp.clip(0, 255).astype(np.uint8).tobytes())
        n += 1
        if n % 25 == 0: print("frame", n, flush=True)
        if limit and n >= limit: break
    out.stdin.close(); out.wait()
    print("done", n)

if __name__ == "__main__":
    main()
