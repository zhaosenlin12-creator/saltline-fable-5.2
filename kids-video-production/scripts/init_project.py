# -*- coding: utf-8 -*-
"""init_project.py - copy the bundled project template to a fresh folder.

    python init_project.py <target-dir> [--force]

Copies project.py, cards.py, anim.py and the empty asset folders. The
template ships with the smart-car example; edit project.py afterwards to
turn it into a new topic.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), "project")

KEEP = ("project.py", "cards.py", "anim.py")
DIRS = ("assets/ai", "assets/real", "build")
# The real-photo starter kit ships with the skill: generic stock shots of
# electronics, soldering and toy cars. The AI illustrations are NOT copied -
# s1_images.py regenerates those for the new topic.
STOCK = "assets/real"


def main():
    argv = sys.argv[1:]
    force = "--force" in argv
    argv = [a for a in argv if not a.startswith("--")]
    if not argv:
        raise SystemExit("usage: init_project.py <target-dir> [--force]")
    target = os.path.abspath(argv[0])
    if os.path.exists(target) and os.listdir(target) and not force:
        raise SystemExit("target exists and is not empty: %s (use --force)" % target)
    os.makedirs(target, exist_ok=True)
    for name in KEEP:
        src = os.path.join(TEMPLATE, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(target, name))
    for d in DIRS:
        os.makedirs(os.path.join(target, d), exist_ok=True)
    src_stock = os.path.join(TEMPLATE, STOCK)
    if os.path.isdir(src_stock):
        for f in os.listdir(src_stock):
            shutil.copy2(os.path.join(src_stock, f),
                         os.path.join(target, "assets", "real", f))
    print("project scaffold ->", target)
    print("stock photos ->", os.path.join(target, "assets", "real"))
    print("next: edit", os.path.join(target, "project.py"))


if __name__ == "__main__":
    main()
