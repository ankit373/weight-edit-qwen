"""table: editor costs on 0.8B (gpu minutes, full-dev scorings, screens) from each workspace's budget log."""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TAB, Values, md_table, p, read_lines, write_text  # noqa: E402

EDITORS = [("editor 0 (gate 4, c02)", "gate4-workspace"), ("editor 1", "gate5-workspace-1"),
           ("editor 2", "gate5-workspace-2"), ("editor 3", "gate5-workspace-3")]
CAP_GPU_MIN, CAP_FULL_DEV = 900, 30  # PROTOCOL.md "budget: max 30 full-dev scorings, max 15 h gpu"
PROTO = "PROTOCOL.md"


def final_claim(rel):
    for i, ln in enumerate(read_lines(rel), 1):
        g = re.search(r"(\d+) of 30 full-dev scorings, ([\d.]+) of 900 gpu min", ln)
        if g:
            return int(g[1]), float(g[2]), i
    raise KeyError(rel)


def main():
    vals = Values()
    for i, ln in enumerate(read_lines(PROTO), 1):
        if "max 30 full-dev scorings, max 15 h gpu" in ln:
            vals.add("cap", "budget per editor", "30 full-dev scorings, 15 h gpu", PROTO, f"line {i}")
            break
    else:
        raise SystemExit("budget line not found in PROTOCOL.md")
    rows, notes = [], []
    for label, ws in EDITORS:
        rel = f"{ws}/logs/budget.tsv"
        with open(p(rel), encoding="utf-8") as f:
            recs = list(csv.DictReader(f, delimiter="\t"))
        gpu = sum(float(r["gpu_min"] or 0) for r in recs)
        full_ok = [r for r in recs if r["kind"] == "full_dev" and r["exit"] == "0"]
        full_bad = [r for r in recs if r["kind"] == "full_dev" and r["exit"] != "0"]
        screens = [r for r in recs if r["kind"] == "dev_subset"]
        by_kind = {}
        for r in recs:
            by_kind[r["kind"]] = by_kind.get(r["kind"], 0.0) + float(r["gpu_min"] or 0)
        fin = f"{ws}/FINAL.md"
        c_full, c_gpu, c_line = final_claim(fin)
        vals.add("gpu_min sum", label, gpu, rel, "sum of gpu_min")
        vals.add("full_dev exit 0", label, len(full_ok), rel, "rows kind=full_dev, exit=0")
        vals.add("full_dev failed", label, len(full_bad), rel, "rows kind=full_dev, exit!=0")
        vals.add("dev_subset rows", label, len(screens), rel, "rows kind=dev_subset")
        for k, v in sorted(by_kind.items()):
            vals.add(f"gpu_min {k}", label, v, rel, f"sum gpu_min, kind={k}")
        vals.add("FINAL.md full-dev", label, c_full, fin, f"line {c_line}")
        vals.add("FINAL.md gpu min", label, c_gpu, fin, f"line {c_line}")
        agree = "yes" if (len(full_ok) == c_full and abs(round(gpu, 1) - c_gpu) < 0.05) else "NO"
        rows.append([label, len(full_ok), f"{gpu:.1f}", f"{100 * gpu / CAP_GPU_MIN:.0f}%",
                     len(screens), f"{by_kind.get('full_dev', 0):.1f}", f"{by_kind.get('nll', 0):.1f}",
                     f"{by_kind.get('dev_subset', 0):.1f}", f"{by_kind.get('other', 0):.1f}",
                     f"{c_full} / {c_gpu}", agree])
        if full_bad:
            notes.append(f"{label}: {len(full_bad)} full-dev row(s) with nonzero exit "
                         f"({', '.join(r['what'] for r in full_bad)}), not counted as a scoring; its gpu minutes "
                         f"are in the total.")
    head = ["editor", "full-dev scorings", "gpu min, total", "of 900 min", "screen runs (200 dev prompts)",
            "gpu min: full dev", "gpu min: NLL", "gpu min: screens", "gpu min: probes and other",
            "FINAL.md says (scorings / gpu min)", "budget log agrees"]
    text = (
        "# editor costs, Qwen3.5-0.8B blind editors\n\n"
        "made by `scripts/tab_costs.py` from each workspace's `logs/budget.tsv` (one row per gpu job, wall-clock "
        "minutes, written by the workspace tools) and the budget line of its `FINAL.md`. cap per editor: "
        f"{CAP_FULL_DEV} full-dev scorings and 15 h ({CAP_GPU_MIN} min) of gpu (`{PROTO}`). a full-dev scoring = a "
        "`full_dev` row with exit 0. gpu minutes are wall clock and include machine sleep stalls the editors noted "
        "(editor 0 about 15 min, editor 1 one sleep inside a full-dev run, editor 3 one sleep during a screen).\n\n" +
        md_table(head, rows) + ("\n" + "\n".join("- " + n for n in notes) + "\n" if notes else "") +
        "\nscreen runs = `dev_subset` rows. editor 2 screened mostly with in-memory probe variants logged as "
        "`other` (for example `probe_v6_screen200`), so its screen count is low and its probe minutes high.\n\n"
        "not in these logs: the test evals of the frozen edits and the gate 3 ReCoVeR runs.\n")
    write_text(os.path.join(TAB, "costs.md"), text)
    vals.write("costs", TAB)
    print("wrote", os.path.join(TAB, "costs.md"))


if __name__ == "__main__":
    main()
