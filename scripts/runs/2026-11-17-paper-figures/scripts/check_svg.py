"""parse every svg as xml and check captions and docs for words and characters the style rules ban."""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OUT  # noqa: E402

BANNED = ["delve", "leverage", "robust", "comprehensive", "seamless", "crucial", "notably", "furthermore",
          "moreover", "showcase", "harness", "landscape", "pivotal", "realm", "unlock"]


def main():
    bad = 0
    for svg in sorted(glob.glob(os.path.join(OUT, "figures", "*.svg"))):
        ET.parse(svg)
    texts = (glob.glob(os.path.join(OUT, "figures", "*.txt")) + glob.glob(os.path.join(OUT, "tables", "*.md")) +
             glob.glob(os.path.join(OUT, "*.md")) + glob.glob(os.path.join(OUT, "figures", "*.svg")))
    for t in sorted(texts):
        s = open(t, encoding="utf-8").read()
        for w in BANNED:
            if re.search(r"\b" + w, s, re.I):
                print("banned word", w, "in", t)
                bad += 1
        if "—" in s or "–" in s:
            print("dash character in", t)
            bad += 1
    print("svg parse ok;", bad, "style problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
