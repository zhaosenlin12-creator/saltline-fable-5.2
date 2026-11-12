# -*- coding: utf-8 -*-
"""s8_final.py - concat the cut, burn the captions, mix the audio, deliver the MP4.

The ass filter breaks on a drive-letter colon, so the subtitle path is passed
relative to the project root and ffmpeg runs with cwd=ROOT.
"""
import os

from common import load_project, run


def main():
    p = load_project()
    concat = os.path.join(p.BUILD, "concat.txt")
    silent = os.path.join(p.BUILD, "video_nosub.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", concat,
         "-c", "copy", silent], "concat")

    subs = "build/subs.ass"
    mix = "build/audio/mix.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", mix,
         "-vf", "ass=%s" % subs,
         "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-profile:v", "high",
         "-level", "4.1", "-pix_fmt", "yuv420p", "-r", "30",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
         "-movflags", "+faststart", "out_final.mp4"], "final render", cwd=p.ROOT)
    tmp = os.path.join(p.ROOT, "out_final.mp4")
    out = os.path.join(p.ROOT, p.OUTPUT_NAME)
    if os.path.exists(out):
        os.remove(out)
    os.replace(tmp, out)
    print("wrote", out)


if __name__ == "__main__":
    main()
