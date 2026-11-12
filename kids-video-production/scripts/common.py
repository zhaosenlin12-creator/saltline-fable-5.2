# -*- coding: utf-8 -*-
"""common.py - project discovery, config loading and ffmpeg helpers.

Every stage script resolves the project root the same way:
  1. $VIDEO_PROJECT env var
  2. --project <dir> on the command line
  3. walk up from the CWD looking for project.py
  4. fall back to the pipeline/ folder that ships with this skill
"""
import os
import sys
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECT = os.path.join(os.path.dirname(SCRIPT_DIR), "project")


def project_root(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if "--project" in argv:
        return os.path.abspath(argv[argv.index("--project") + 1])
    env = os.environ.get("VIDEO_PROJECT")
    if env:
        return os.path.abspath(env)
    here = os.path.abspath(os.getcwd())
    while True:
        if os.path.exists(os.path.join(here, "project.py")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    if os.path.exists(os.path.join(DEFAULT_PROJECT, "project.py")):
        return DEFAULT_PROJECT
    raise SystemExit(
        "project not found. Pass --project <dir>, set $VIDEO_PROJECT, or run "
        "inside a folder that contains project.py")


def load_project(root=None):
    """Import the project's project.py as a module and return it."""
    root = root or project_root()
    for d in (SCRIPT_DIR, root):
        if d not in sys.path:
            sys.path.insert(0, d)
    import importlib
    import project
    importlib.reload(project)
    project.ROOT = root
    project.BUILD = os.path.join(root, "build")
    project.AI = os.path.join(root, "assets", "ai")
    project.REAL = os.path.join(root, "assets", "real")
    for d in (project.BUILD, project.AI, project.REAL):
        os.makedirs(d, exist_ok=True)
    return project


def run(cmd, label=None, cwd=None, quiet=False):
    """Run a subprocess and surface stderr as a hard failure."""
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=cwd)
    if r.returncode != 0:
        if label:
            print("FAILED:", label)
        print((r.stderr or "")[-2500:])
        raise SystemExit(1)
    if not quiet and label:
        print("  ok:", label)
    return r.stdout


def dec(cmd):
    """Run a command and return stdout as text (for ffprobe)."""
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def probe_duration(path):
    out = dec(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", path])
    return float(out.strip())


def probe_frames(path):
    out = dec(["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-count_frames", "-show_entries", "stream=nb_read_frames",
               "-of", "csv=p=0", path])
    try:
        return int(out.strip())
    except ValueError:
        out = dec(["ffprobe", "-v", "error", "-select_streams", "v:0",
                   "-show_entries", "stream=nb_frames", "-of", "csv=p=0", path])
        return int(out.strip())


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def api_keys():
    """Every MiniMax-compatible key we can find, best first.

    The imagegen skill key is tried first; the account key in
    ~/.codex/auth.json is a second shot for when the first one has run out
    of Token Plan allowance on the TTS endpoint.
    """
    out = []
    for p in (os.environ.get("MINIMAX_KEY_FILE", ""),
              os.path.expanduser("~/.codex/skills/minimax-imagegen/key.txt"),
              os.path.expanduser("~/skills/minimax-imagegen/key.txt")):
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                k = f.read().strip()
            if k and k not in out:
                out.append(k)
    env = os.environ.get("MINIMAX_API_KEY")
    if env and env not in out:
        out.append(env)
    auth = os.path.expanduser("~/.codex/auth.json")
    if os.path.exists(auth):
        try:
            import json
            with open(auth, encoding="utf-8") as f:
                k = (json.load(f).get("OPENAI_API_KEY") or "").strip()
            if k and k not in out:
                out.append(k)
        except Exception:
            pass
    return out


def api_key():
    """The default MiniMax API key, reused from the installed imagegen skill."""
    ks = api_keys()
    if not ks:
        raise SystemExit("MiniMax API key not found (expected minimax-imagegen/key.txt)")
    return ks[0]
