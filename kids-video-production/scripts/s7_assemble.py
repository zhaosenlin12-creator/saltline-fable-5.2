# -*- coding: utf-8 -*-
"""s7_assemble.py - render still cards into moving segments, then cut the film.

Each narration beat becomes exactly one visual segment. Static cards get a
gentle Ken Burns via ffmpeg zoompan; animated segments are copied straight in.
The result records a per-line A/V delta so the caption pass can realign.
"""
import os
import sys
import json
import subprocess

from common import load_project, load_json, dump_json, run, probe_frames

# gentle Ken Burns: in / out / in-with-pan, cycled so no two cuts feel alike
MOTION = [
    dict(z0=1.00, z1=1.05, px=0.0, py=0.0),
    dict(z0=1.05, z1=1.00, px=0.0, py=0.0),
    dict(z0=1.01, z1=1.05, px=45.0, py=0.0),
    dict(z0=1.05, z1=1.01, px=-38.0, py=25.0),
    dict(z0=1.00, z1=1.04, px=0.0, py=-35.0),
    dict(z0=1.01, z1=1.05, px=32.0, py=28.0),
]


def render_static(out, card_png, nframes, motion, w=1080, h=1920, fps=30):
    n1 = max(1, nframes - 1)
    z0, z1, px, py = motion["z0"], motion["z1"], motion["px"], motion["py"]
    z = "%s+(%s-%s)*on/%d" % (z0, z1, z0, n1)
    x = "iw/2-(iw/zoom/2)+(%s)*(on/%d-0.5)" % (px, n1)
    y = "ih/2-(ih/zoom/2)+(%s)*(on/%d-0.5)" % (py, n1)
    # 原图就是成品分辨率，不再先放大 2 倍（那会把 720p 卡片拉糊）
    vf = ("scale=%d:%d:flags=lanczos,zoompan=z='%s':x='%s':y='%s':d=1:s=%dx%d:fps=%d,format=yuv420p"
          % (w, h, z, x, y, w, h, fps))
    cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", card_png,
           "-vf", vf, "-frames:v", str(nframes),
           "-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-pix_fmt", "yuv420p", out]
    run(cmd, "static render " + os.path.basename(out))
    return out


def main():
    p = load_project()
    segdir = os.path.join(p.BUILD, "seg")
    os.makedirs(segdir, exist_ok=True)
    cards_dir = os.path.join(p.BUILD, "cards")
    anim_dir = os.path.join(p.BUILD, "anim")

    plan, total = p.build_plan()
    final = []
    for i, seg in enumerate(plan):
        name = seg["name"]
        target = max(1, int(round(seg["dur"] * 30)))
        if i == 0:
            # hold the cover through the narration lead-in so A/V stay locked
            target += int(round(plan[0]["start"] * 30))
        if seg["kind"] == "anim":
            src = os.path.join(anim_dir, name + ".mp4")
            dst = os.path.join(segdir, name + ".mp4")
            if not os.path.exists(src):
                raise SystemExit("missing animation: " + src)
            if os.path.exists(dst):
                os.remove(dst)
            run(["ffmpeg", "-y", "-v", "error", "-i", src, "-c", "copy", dst], "copy " + name)
            path = dst
        else:
            card = os.path.join(cards_dir, name + ".png")
            if not os.path.exists(card):
                raise SystemExit("missing card: " + card)
            path = render_static(os.path.join(segdir, name + ".mp4"), card,
                                 target, MOTION[i % len(MOTION)], w=p.W, h=p.H)
        nf = probe_frames(path)
        final.append({"name": name, "path": path, "nframes": nf,
                      "dur": round(nf / 30.0, 3), "line": seg["line"]})

    vt = 0.0
    for f in final:
        f["vstart"] = round(vt, 3)
        vt += f["dur"]
    tl = load_json(os.path.join(p.BUILD, "timeline.json"))
    nstart = {l["id"]: l["start"] for l in tl["lines"]}
    for f in final:
        f["delta"] = round(f["vstart"] - nstart[f["line"]], 3)

    dump_json(os.path.join(p.BUILD, "segments_final.json"),
              {"total": round(vt, 3), "segments": final})
    with open(os.path.join(p.BUILD, "concat.txt"), "w", encoding="utf-8") as fh:
        for f in final:
            fh.write("file '" + f["path"].replace("\\", "/") + "'\n")

    print("segments: %d  video total %.3fs (narration %.3fs)" % (len(final), vt, total))
    for f in final:
        print("  %-16s %4df  vstart %7.2f  delta %+.3f"
              % (f["name"], f["nframes"], f["vstart"], f["delta"]))


if __name__ == "__main__":
    main()
