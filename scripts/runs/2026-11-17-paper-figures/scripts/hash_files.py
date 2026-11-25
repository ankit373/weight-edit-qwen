"""sha256 of every input file named in the values files, and of every output. writes input_sha256.txt, output_sha256.txt."""
import glob
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OUT, ROOT  # noqa: E402


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    srcs = set()
    for tsv in glob.glob(os.path.join(OUT, "figures", "*.values.tsv")) + glob.glob(os.path.join(OUT, "tables", "*.values.tsv")):
        with open(tsv, encoding="utf-8") as f:
            next(f)
            for line in f:
                for s in line.rstrip("\n").split("\t")[3].split("; "):
                    s = s.split(" [")[0].split(" (")[0].strip()
                    if s and os.path.isfile(os.path.join(ROOT, s)):
                        srcs.add(s)
    with open(os.path.join(OUT, "input_sha256.txt"), "w") as f:
        for s in sorted(srcs):
            f.write(f"{sha(os.path.join(ROOT, s))}  {s}\n")
    outs = sorted(glob.glob(os.path.join(OUT, "figures", "*")) + glob.glob(os.path.join(OUT, "tables", "*")) +
                  glob.glob(os.path.join(OUT, "scripts", "*.py")) + glob.glob(os.path.join(OUT, "scripts", "*.sh")))
    with open(os.path.join(OUT, "output_sha256.txt"), "w") as f:
        for o in outs:
            f.write(f"{sha(o)}  {os.path.relpath(o, ROOT)}\n")
    print(len(srcs), "inputs,", len(outs), "outputs")


if __name__ == "__main__":
    main()
