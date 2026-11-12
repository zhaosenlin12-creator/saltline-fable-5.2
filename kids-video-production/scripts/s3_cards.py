# -*- coding: utf-8 -*-
"""s3_cards.py - build the static 1080x1920 cards for every segment.

The card art is project-specific, so the project supplies a `cards.py` module
exposing build_cards() -> dict{name: PIL.Image}. This stage handles the
plumbing: crop cache, output directory, and saving.

Project cards.py contract:
    from design import *
    def build_cards():
        out = {}
        img = paper().convert("RGBA")
        ...
        out["v01_cover"] = img
        return out
"""
import os
import importlib
import sys

from common import load_project, run


def main():
    p = load_project()
    if p.ROOT not in sys.path:
        sys.path.insert(0, p.ROOT)
    cards_dir = os.path.join(p.BUILD, "cards")
    os.makedirs(cards_dir, exist_ok=True)
    crop_dir = os.path.join(p.BUILD, "crop")
    os.makedirs(crop_dir, exist_ok=True)

    # reload first, then point the crop cache at this project's build dir:
    # importlib.reload resets design.CROPDIR back to None.
    import design
    importlib.reload(design)
    design.set_cropdir(crop_dir)
    import cards
    importlib.reload(cards)

    built = cards.build_cards()
    for name, img in built.items():
        img.convert("RGB").save(os.path.join(cards_dir, name + ".png"), quality=95)
        print("  card", name)
    print("cards done ->", cards_dir)


if __name__ == "__main__":
    main()
