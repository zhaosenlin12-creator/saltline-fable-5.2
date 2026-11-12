# -*- coding: utf-8 -*-
"""s4_anim.py - render the animated segments (code reveal, flow, live demo).

The animation art is project-specific, so the project supplies an `anim.py`
module exposing build_anims(segdur) -> dict{name: path}. segdur maps segment
name -> duration in seconds, taken from the narration timeline so animation
length always matches the voice.

Streaming frames: write RGB bytes straight into ffmpeg's stdin rather than
buffering PNGs. Use the SegWriter helper copied from this skill's design.py
patterns, or any equivalent.
"""
import os
import importlib
import sys

from common import load_project


def main():
    p = load_project()
    if p.ROOT not in sys.path:
        sys.path.insert(0, p.ROOT)
    anim_dir = os.path.join(p.BUILD, "anim")
    os.makedirs(anim_dir, exist_ok=True)

    # reload first, then point the crop cache at this project's build dir:
    # importlib.reload resets design.CROPDIR back to None.
    import design
    importlib.reload(design)
    design.set_cropdir(os.path.join(p.BUILD, "crop"))
    import anim
    importlib.reload(anim)

    segdur = p.segment_durations()
    out = anim.build_anims(segdur)
    for name in sorted(out):
        print("  anim", name)
    print("animations done ->", anim_dir)


if __name__ == "__main__":
    main()
