# part C figures

made 2026-11-24. cpu only, python stdlib only, sandboxed, no model, no network. run folders were read only.

rebuild from the project root:

```
sh runs/2026-11-24-partc-figures/scripts/run_all.sh
```

`scripts/common.py` loads the 2026-11-17 `common.py` (readers and svg code) and adds the part C paths and a forest-plot helper. every figure has an `.svg`, a one-line caption `.txt` and a `.values.tsv` with each plotted number, its source file and field.

| file | script | source |
|---|---|---|
| figures/figc1_crossling_gain | scripts/figc1_crossling_gain.py | `runs/2026-11-22-partc-run/scores/{08,2b}/{m-arenahard,lcb-greedy,lcb-long}/stats.json`, `scores/nc-sa/xl-alpacaeval/{08,2b}/stats.json` (`comparisons.*_vs_baseline.unscored_drop.lpr`) |
| figures/figc2_damage | scripts/figc2_damage.py | `runs/2026-11-22-partc-run/scores/{08,2b}/{global-mmlu,mgsm,ifeval}/stats.json` (`comparisons.*_vs_baseline.all`, `.damage.label`) |
| figures/figc3_judge_2b | scripts/figc3_judge_2b.py | `runs/2026-11-24-judge-2b/analysis/results.json` (`all.methods.*.weighted`, `all.diffs`, `high.diffs`) |
| tables/partc_numbers.md | scripts/extract.py | every part C stats.json and guard.json, plus plain counts of per-row flags (`scored` = 0, `starts_with_old` = 1). no new statistics |
