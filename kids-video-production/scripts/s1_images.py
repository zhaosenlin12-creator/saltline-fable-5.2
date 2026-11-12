# -*- coding: utf-8 -*-
"""s1_images.py - generate style-matched illustrations via MiniMax image-01.

Reads SHOTS from project.py. Each shot is (filename_stem, prompt). Cached:
an existing file over 20KB is skipped, so re-running is cheap.
"""
import os
import time
import concurrent.futures as cf
import requests

from common import load_project, api_key, api_keys

API = "https://api.minimaxi.com/v1/image_generation"


def gen(out_dir, name, prompt, style, aspect="9:16", model="image-01"):
    path = os.path.join(out_dir, name + ".png")
    if os.path.exists(path) and os.path.getsize(path) > 20000:
        return name + ": cached"
    body = {"model": model, "prompt": (style + ". " + prompt).strip(),
            "aspect_ratio": aspect}
    # a key can run out of Token Plan allowance, so try every key we know
    for attempt in range(4):
        for key in api_keys():
            try:
                r = requests.post(API, json=body,
                                  headers={"Authorization": "Bearer " + key,
                                           "Content-Type": "application/json"},
                                  timeout=240)
                r.raise_for_status()
                j = r.json()
                if j.get("base_resp", {}).get("status_code") not in (0, None):
                    raise RuntimeError(repr(j.get("base_resp")))
                url = j["data"]["image_urls"][0]
                data = requests.get(url, timeout=120)
                data.raise_for_status()
                with open(path, "wb") as f:
                    f.write(data.content)
                return "%s: ok %dB" % (name, len(data.content))
            except Exception as e:
                print("  img retry (key %s): %s" % (key[:8], e), flush=True)
        if attempt == 3:
            return "%s: FAILED" % name
        time.sleep(3 + attempt * 3)
    return name + ": FAILED"


def main():
    p = load_project()
    style = p.IMAGE_STYLE
    aspect = getattr(p, "IMAGE_ASPECT", "9:16")
    model = getattr(p, "IMAGE_MODEL", "image-01")
    shots = p.SHOTS
    print("generating %d illustrations..." % len(shots))
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(gen, p.AI, n, pr, style, aspect, model)
                for n, pr in shots]
        for f in cf.as_completed(futs):
            print("  ", f.result(), flush=True)
    print("images done ->", p.AI)


if __name__ == "__main__":
    main()
