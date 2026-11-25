"""shared helpers for the paper figure scripts: paths, run-file readers, plain svg drawing. stdlib only."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(OUT))
FIG = os.path.join(OUT, "figures")
TAB = os.path.join(OUT, "tables")

LANGS = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]
FONT = "Helvetica, Arial, sans-serif"


def p(rel):
    """absolute path of a project-relative path."""
    return os.path.join(ROOT, rel)


def load(rel):
    with open(p(rel), encoding="utf-8") as f:
        return json.load(f)


def read_lines(rel):
    with open(p(rel), encoding="utf-8") as f:
        return f.read().splitlines()


def score_row(rel, source, lang="all"):
    """one row of a score.py json (list of cells). lpr in percent, plus n and n_scored."""
    for r in load(rel):
        if r["source"] == source and r["language"] == lang:
            return {"lpr": 100.0 * r["lpr"], "n": r["n"], "n_scored": r["n_scored"]}
    raise KeyError((rel, source, lang))


def full_pct(score_rel, wrong_rel, source):
    """full-failure % as numbers.md 'FP': full_response_wrong rows of the source / n_scored of that source."""
    src = None if source == "all" else source
    n_full = 0
    for r in load(wrong_rel)["failing_responses"]:
        if r.get("full_response_wrong") and (src is None or r["id"].split("/")[1] == src):
            n_full += 1
    n_scored = score_row(score_rel, source)["n_scored"]
    return 100.0 * n_full / n_scored, n_full, n_scored


def guard(rel):
    return load(rel)


class Values:
    """every plotted number with its source, written next to the figure as a tsv."""

    def __init__(self):
        self.rows = []

    def add(self, panel, label, value, source, field):
        self.rows.append((panel, label, value, source, field))
        return value

    def write(self, name, folder=None):
        path = os.path.join(folder or FIG, name + ".values.tsv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("panel\tlabel\tvalue\tsource\tfield\n")
            for a, b, v, s, fl in self.rows:
                vs = "" if v is None else (repr(v) if isinstance(v, float) else str(v))
                f.write(f"{a}\t{b}\t{vs}\t{s}\t{fl}\n")
        return path


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text if text.endswith("\n") else text + "\n")


# ---------- svg ----------

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def f1(x):
    return f"{x:.1f}"


class Svg:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, size=11, anchor="start", weight="normal", fill="#000", rotate=None, italic=False):
        tr = f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate is not None else ""
        st = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
                 f'font-weight="{weight}" fill="{fill}"{st}{tr}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke="#000", width=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
                 f'stroke-width="{width}"{d}/>')

    def rect(self, x, y, w, h, fill="none", stroke="#000", width=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{width}"{d}/>')

    def polyline(self, pts, stroke="#000", width=1.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polyline points="{s}" fill="none" stroke="{stroke}" stroke-width="{width}"{d}/>')

    def marker(self, x, y, shape, filled=True, r=4.5, color="#000"):
        fill = color if filled else "#fff"
        if shape == "circle":
            self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{color}" stroke-width="1.3"/>')
        elif shape == "square":
            self.rect(x - r, y - r, 2 * r, 2 * r, fill=fill, stroke=color, width=1.3)
        elif shape in ("triangle", "triangle_down"):
            k = -1 if shape == "triangle_down" else 1
            pts = [(x, y - k * r * 1.15), (x - r * 1.1, y + k * r * 0.85), (x + r * 1.1, y + k * r * 0.85)]
            s = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
            self.add(f'<polygon points="{s}" fill="{fill}" stroke="{color}" stroke-width="1.3"/>')
        elif shape == "diamond":
            pts = [(x, y - r * 1.25), (x + r * 1.1, y), (x, y + r * 1.25), (x - r * 1.1, y)]
            s = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
            self.add(f'<polygon points="{s}" fill="{fill}" stroke="{color}" stroke-width="1.3"/>')
        elif shape == "plus":
            self.line(x - r, y, x + r, y, stroke=color, width=1.8)
            self.line(x, y - r, x, y + r, stroke=color, width=1.8)
        elif shape == "cross":
            self.line(x - r, y - r, x + r, y + r, stroke=color, width=1.8)
            self.line(x - r, y + r, x + r, y - r, stroke=color, width=1.8)
        else:
            raise ValueError(shape)

    def save(self, path):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">'
                f'<rect width="100%" height="100%" fill="white"/>')
        with open(path, "w", encoding="utf-8") as f:
            f.write(head + "\n" + "\n".join(self.parts) + "\n</svg>\n")


def lin(v, v0, v1, p0, p1):
    return p0 + (v - v0) * (p1 - p0) / (v1 - v0)


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out) + "\n"
