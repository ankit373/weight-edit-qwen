# part C numbers, reformatted from the run files

made by `runs/2026-11-24-partc-figures/scripts/extract.py`. values are copied from each stats.json (`observed`, `comparisons`) and guard.json; the only new arithmetic is counting per-row flags (`scored` = 0 in `*.perrow.jsonl`, `starts_with_old` = 1 in `*.loops.jsonl`). CIs are 95% paired cluster bootstrap, p is the group-swap permutation p, both from stats_c.py.

## 08 m-arenahard (`runs/2026-11-22-partc-run/scores/08/m-arenahard/stats.json`, rows 700, clusters 50)

| method | lpr drop | lpr fail | lpr pass | full % drop | wpr | late switch % | loop % | cap % | unscored (count of scored=0 in perrow) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 86.3 | 86.1 | 86.3 | 2.86 | 79.9 | 10.2 | 0.71 | 100.0 | 1 of 700 |
| c02_nb_L15u1047_k2 | 91.4 | 91.1 | 91.4 | 0.43 | 82.5 | 8.0 | 0.86 | 99.9 | 2 of 700 |
| h5_a2_n5 | 88.7 | 88.4 | 88.7 | 0.72 | 80.7 | 10.2 | 1.29 | 100.0 | 2 of 700 |
| mix21_22b0.75_23b0.5 | 90.7 | 90.6 | 90.7 | 1.00 | 84.1 | 8.3 | 1.57 | 100.0 | 1 of 700 |
| combo_a14_b14 | 90.1 | 89.7 | 90.1 | 0.57 | 81.5 | 9.3 | 1.71 | 99.9 | 3 of 700 |
| recover | 90.1 | 89.9 | 90.1 | 0.14 | 88.7 | 9.3 | 1.14 | 100.0 | 2 of 700 |
| instr_end | 85.7 | 85.4 | 85.7 | 0.86 | 82.9 | 12.9 | 0.29 | 99.9 | 2 of 700 |

| a vs b | lpr drop | lpr fail | lpr pass | full % drop | loop % drop | mcnemar a better / b better, p |
|---|---|---|---|---|---|---|
| recover_vs_baseline | +3.9 [+0.3, +7.8] p 0.0461 | +3.7 [+0.3, +7.4] p 0.0506 | +3.9 [+0.3, +7.9] p 0.0505 | -2.7 [-6.6, -0.4] p 0.0166 | +0.4 [-0.3, +1.3] p 0.5309 | 71 / 45, 0.0199 |
| instr_end_vs_baseline | -0.6 [-3.3, +2.1] p 0.7049 | -0.7 [-3.6, +2.1] p 0.6959 | -0.6 [-3.3, +2.1] p 0.7596 | -2.0 [-5.9, +0.4] p 0.2970 | -0.4 [-1.1, +0.3] p 0.4598 | 49 / 52, 0.8424 |
| c02_nb_L15u1047_k2_vs_baseline | +5.1 [+1.3, +9.6] p 0.0147 | +5.0 [+1.1, +9.4] p 0.0208 | +5.1 [+1.3, +9.6] p 0.0178 | -2.4 [-5.9, -0.4] p 0.0325 | +0.1 [-0.7, +1.0] p 1.0000 | 73 / 37, 0.0008 |
| c02_nb_L15u1047_k2_vs_recover | +1.3 [-1.0, +3.6] p 0.2776 | +1.3 [-1.0, +3.6] p 0.3315 | +1.3 [-1.0, +3.6] p 0.3256 | +0.3 [-0.3, +1.0] p 0.5014 | -0.3 [-1.1, +0.6] p 0.7579 | 50 / 42, 0.4657 |
| c02_nb_L15u1047_k2_vs_instr_end | +5.7 [+2.1, +9.5] p 0.0038 | +5.7 [+2.1, +9.6] p 0.0047 | +5.7 [+2.1, +9.6] p 0.0048 | -0.4 [-1.1, +0.3] p 0.3199 | +0.6 [-0.1, +1.4] p 0.2858 | 77 / 38, 0.0004 |
| h5_a2_n5_vs_baseline | +2.4 [-1.3, +6.7] p 0.2388 | +2.3 [-1.4, +6.6] p 0.3133 | +2.4 [-1.3, +6.7] p 0.2753 | -2.1 [-5.4, -0.1] p 0.0934 | +0.6 [-0.4, +1.7] p 0.4715 | 62 / 44, 0.0982 |
| h5_a2_n5_vs_recover | -1.4 [-4.3, +1.4] p 0.3695 | -1.4 [-4.3, +1.4] p 0.3885 | -1.4 [-4.3, +1.4] p 0.3857 | +0.6 [-0.1, +1.4] p 0.2535 | +0.1 [-1.0, +1.3] p 1.0000 | 47 / 57, 0.3776 |
| h5_a2_n5_vs_instr_end | +3.0 [-0.3, +6.6] p 0.0918 | +3.0 [-0.3, +6.6] p 0.1159 | +3.0 [-0.3, +6.6] p 0.1047 | -0.1 [-1.0, +0.7] p 0.8551 | +1.0 [+0.1, +2.0] p 0.0966 | 61 / 40, 0.0460 |
| mix21_22b0.75_23b0.5_vs_baseline | +4.4 [+1.8, +7.2] p 0.0041 | +4.4 [+1.9, +7.1] p 0.0043 | +4.4 [+1.9, +7.1] p 0.0043 | -1.9 [-4.3, -0.3] p 0.0335 | +0.9 [+0.0, +1.7] p 0.1086 | 56 / 25, 0.0008 |
| mix21_22b0.75_23b0.5_vs_recover | +0.6 [-2.9, +3.6] p 0.7268 | +0.7 [-2.6, +3.6] p 0.7363 | +0.6 [-3.0, +3.6] p 0.8238 | +0.9 [-0.1, +2.6] p 0.4974 | +0.4 [-0.6, +1.3] p 0.5426 | 46 / 41, 0.6683 |
| mix21_22b0.75_23b0.5_vs_instr_end | +5.0 [+2.4, +7.6] p 0.0007 | +5.1 [+2.4, +7.9] p 0.0007 | +5.0 [+2.4, +7.7] p 0.0008 | +0.1 [-1.0, +1.7] p 0.9724 | +1.3 [+0.3, +2.3] p 0.0343 | 63 / 29, 0.0005 |
| combo_a14_b14_vs_baseline | +3.8 [+0.7, +7.3] p 0.0282 | +3.6 [+0.4, +6.9] p 0.0413 | +3.9 [+0.7, +7.3] p 0.0304 | -2.3 [-5.0, -0.6] p 0.0088 | +1.0 [+0.0, +2.0] p 0.1232 | 61 / 34, 0.0073 |
| combo_a14_b14_vs_recover | -0.0 [-3.2, +3.1] p 0.9794 | -0.1 [-3.1, +2.7] p 1.0000 | +0.0 [-3.1, +3.1] p 1.0000 | +0.4 [-0.4, +1.7] p 0.7477 | +0.6 [-0.6, +1.7] p 0.4561 | 48 / 48, 1.0000 |
| combo_a14_b14_vs_instr_end | +4.4 [+1.4, +7.5] p 0.0064 | +4.3 [+1.3, +7.4] p 0.0092 | +4.4 [+1.4, +7.6] p 0.0084 | -0.3 [-1.3, +0.9] p 0.7595 | +1.4 [+0.4, +2.6] p 0.0202 | 66 / 36, 0.0039 |

per-language cells with a CI that excludes 0 (drop rule): recover_vs_baseline de +14.0 [+6.0, +24.0]; recover_vs_baseline tr +8.0 [+2.0, +16.0]; instr_end_vs_baseline hi -10.0 [-18.0, -2.0]; c02_nb_L15u1047_k2_vs_baseline de +14.0 [+6.0, +24.0]; c02_nb_L15u1047_k2_vs_baseline it +16.0 [+6.0, +26.0]; c02_nb_L15u1047_k2_vs_baseline vi +12.0 [+4.0, +22.0]; c02_nb_L15u1047_k2_vs_instr_end de +10.0 [+2.0, +20.0]; c02_nb_L15u1047_k2_vs_instr_end hi +12.0 [+2.0, +22.0]; c02_nb_L15u1047_k2_vs_instr_end it +12.0 [+2.0, +22.0]; c02_nb_L15u1047_k2_vs_instr_end vi +10.0 [+2.0, +18.0]; h5_a2_n5_vs_baseline pt +12.0 [+4.0, +22.0]; h5_a2_n5_vs_recover tr -8.0 [-16.0, -2.0]; h5_a2_n5_vs_instr_end ja +13.8 [+3.7, +25.8]; mix21_22b0.75_23b0.5_vs_baseline ja +14.0 [+6.0, +24.0]; mix21_22b0.75_23b0.5_vs_recover hi +8.0 [+2.0, +16.0]; mix21_22b0.75_23b0.5_vs_instr_end es +10.0 [+2.0, +20.0]; mix21_22b0.75_23b0.5_vs_instr_end hi +14.0 [+6.0, +24.0]; mix21_22b0.75_23b0.5_vs_instr_end ja +16.0 [+4.0, +30.0]; combo_a14_b14_vs_baseline it +16.0 [+6.0, +26.0]; combo_a14_b14_vs_instr_end it +12.0 [+2.0, +22.0]; combo_a14_b14_vs_instr_end ja +11.8 [+3.8, +21.8]

guard vs baseline (baseline loop % 0.71, mean NLL 0.700):

| method | loop % (change) | mean NLL (change) | empty % | guard | source |
|---|---|---|---|---|---|
| c02_nb_L15u1047_k2 | 0.86 (+0.14) | 0.841 (+0.141) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/08/m-arenahard/c02_nb_L15u1047_k2.guard.json` |
| h5_a2_n5 | 1.29 (+0.57) | 0.827 (+0.127) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/08/m-arenahard/h5_a2_n5.guard.json` |
| mix21_22b0.75_23b0.5 | 1.57 (+0.86) | 0.771 (+0.071) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/08/m-arenahard/mix21_22b0.75_23b0.5.guard.json` |
| combo_a14_b14 | 1.71 (+1.00) | 0.770 (+0.070) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/08/m-arenahard/combo_a14_b14.guard.json` |
| recover | 1.14 (+0.43) | 0.876 (+0.176) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/08/m-arenahard/recover.guard.json` |
| instr_end | 0.29 (-0.43) | 0.712 (+0.012) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/08/m-arenahard/instr_end.guard.json` |

## 08 xl-alpacaeval (`runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/08/stats.json`, rows 980, clusters 70)

| method | lpr drop | lpr fail | lpr pass | full % drop | wpr | late switch % | loop % | cap % | unscored (count of scored=0 in perrow) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 84.5 | 84.4 | 84.6 | 3.27 | 82.3 | 11.8 | 1.94 | 94.1 | 2 of 980 |
| c02_nb_L15u1047_k2 | 93.1 | 92.7 | 93.2 | 0.41 | 84.8 | 5.8 | 2.65 | 93.2 | 5 of 980 |
| h5_a2_n5 | 86.1 | 85.6 | 86.1 | 1.95 | 84.5 | 11.1 | 2.55 | 92.3 | 5 of 980 |
| mix21_22b0.75_23b0.5 | 88.9 | 88.5 | 88.9 | 0.61 | 89.9 | 10.1 | 4.39 | 94.8 | 4 of 980 |
| combo_a14_b14 | 89.8 | 89.5 | 89.8 | 0.61 | 87.4 | 8.9 | 3.37 | 93.9 | 3 of 980 |
| recover | 92.1 | 91.8 | 92.1 | 0.31 | 91.3 | 7.1 | 1.94 | 95.1 | 3 of 980 |
| instr_end | 86.6 | 86.0 | 86.6 | 1.33 | 86.6 | 11.8 | 2.24 | 91.8 | 6 of 980 |

| a vs b | lpr drop | lpr fail | lpr pass | full % drop | loop % drop | mcnemar a better / b better, p |
|---|---|---|---|---|---|---|
| recover_vs_baseline | +7.6 [+4.1, +11.5] p 0.0001 | +7.4 [+3.9, +11.4] p 0.0002 | +7.6 [+4.1, +11.4] p 0.0002 | -3.0 [-4.2, -1.8] p 0.0001 | +0.0 [-1.0, +1.0] p 1.0000 | 113 / 39, 0.0000 |
| instr_end_vs_baseline | +2.0 [-0.5, +4.6] p 0.1209 | +1.6 [-0.9, +4.3] p 0.2599 | +2.0 [-0.4, +4.6] p 0.1300 | -1.9 [-3.2, -0.7] p 0.0051 | +0.3 [-0.7, +1.3] p 0.7103 | 76 / 57, 0.1182 |
| c02_nb_L15u1047_k2_vs_baseline | +8.6 [+5.3, +12.2] p 0.0001 | +8.3 [+4.9, +11.8] p 0.0001 | +8.6 [+5.3, +12.1] p 0.0001 | -2.9 [-4.3, -1.6] p 0.0001 | +0.7 [-0.3, +1.7] p 0.2336 | 115 / 31, 0.0000 |
| c02_nb_L15u1047_k2_vs_recover | +1.0 [-0.8, +2.8] p 0.2794 | +0.8 [-1.1, +2.7] p 0.4748 | +1.0 [-0.7, +2.8] p 0.3202 | +0.1 [-0.2, +0.4] p 0.5261 | +0.7 [-0.6, +2.0] p 0.3737 | 56 / 46, 0.3729 |
| c02_nb_L15u1047_k2_vs_instr_end | +6.6 [+3.9, +9.5] p 0.0001 | +6.6 [+3.8, +9.7] p 0.0002 | +6.5 [+3.8, +9.4] p 0.0002 | -0.9 [-1.8, -0.2] p 0.0383 | +0.4 [-0.6, +1.4] p 0.5439 | 94 / 30, 0.0000 |
| h5_a2_n5_vs_baseline | +1.5 [-1.3, +4.5] p 0.3166 | +1.2 [-1.8, +4.4] p 0.4872 | +1.5 [-1.2, +4.5] p 0.3402 | -1.3 [-2.9, +0.1] p 0.1100 | +0.6 [-0.4, +1.6] p 0.3356 | 86 / 71, 0.2638 |
| h5_a2_n5_vs_recover | -6.1 [-9.0, -3.3] p 0.0002 | -6.2 [-9.2, -3.5] p 0.0002 | -6.0 [-8.9, -3.3] p 0.0002 | +1.6 [+0.8, +2.7] p 0.0003 | +0.6 [-0.7, +2.0] p 0.4921 | 43 / 102, 0.0000 |
| h5_a2_n5_vs_instr_end | -0.5 [-2.6, +1.7] p 0.6805 | -0.4 [-2.6, +1.7] p 0.7812 | -0.5 [-2.7, +1.6] p 0.7099 | +0.6 [-0.6, +1.9] p 0.3962 | +0.3 [-0.8, +1.5] p 0.7383 | 70 / 75, 0.7399 |
| mix21_22b0.75_23b0.5_vs_baseline | +4.3 [+2.2, +6.6] p 0.0003 | +4.1 [+1.8, +6.4] p 0.0010 | +4.3 [+2.1, +6.5] p 0.0003 | -2.7 [-4.0, -1.4] p 0.0001 | +2.4 [+1.1, +3.8] p 0.0004 | 77 / 36, 0.0001 |
| mix21_22b0.75_23b0.5_vs_recover | -3.3 [-5.9, -0.8] p 0.0138 | -3.4 [-6.0, -0.9] p 0.0138 | -3.3 [-5.9, -0.8] p 0.0164 | +0.3 [-0.1, +0.8] p 0.2195 | +2.4 [+0.9, +4.1] p 0.0041 | 35 / 67, 0.0020 |
| mix21_22b0.75_23b0.5_vs_instr_end | +2.3 [+0.2, +4.6] p 0.0421 | +2.4 [+0.1, +4.9] p 0.0552 | +2.2 [+0.1, +4.5] p 0.0611 | -0.7 [-1.5, -0.1] p 0.0689 | +2.1 [+0.8, +3.6] p 0.0057 | 71 / 48, 0.0433 |
| combo_a14_b14_vs_baseline | +5.2 [+2.7, +7.8] p 0.0004 | +5.1 [+2.6, +7.7] p 0.0005 | +5.2 [+2.7, +7.8] p 0.0004 | -2.7 [-4.1, -1.4] p 0.0001 | +1.4 [+0.1, +2.9] p 0.0734 | 85 / 34, 0.0000 |
| combo_a14_b14_vs_recover | -2.3 [-5.1, +0.2] p 0.0975 | -2.3 [-5.1, +0.2] p 0.1052 | -2.3 [-5.1, +0.2] p 0.1109 | +0.3 [-0.3, +1.0] p 0.4677 | +1.4 [+0.2, +2.8] p 0.0412 | 46 / 68, 0.0487 |
| combo_a14_b14_vs_instr_end | +3.2 [+1.0, +5.4] p 0.0050 | +3.5 [+1.2, +5.7] p 0.0046 | +3.2 [+1.0, +5.3] p 0.0071 | -0.7 [-1.7, +0.2] p 0.1280 | +1.1 [-0.4, +2.8] p 0.2243 | 77 / 45, 0.0048 |

per-language cells with a CI that excludes 0 (drop rule): recover_vs_baseline ar +10.0 [+2.9, +17.1]; recover_vs_baseline es +14.3 [+7.1, +22.9]; recover_vs_baseline it +11.4 [+4.3, +20.0]; recover_vs_baseline ja +14.5 [+4.5, +24.6]; recover_vs_baseline ko +11.4 [+2.9, +20.0]; recover_vs_baseline ru +10.0 [+4.3, +17.1]; recover_vs_baseline tr +8.4 [+1.2, +16.9]; recover_vs_baseline vi +8.6 [+2.9, +15.7]; instr_end_vs_baseline es +8.6 [+1.4, +17.1]; instr_end_vs_baseline vi +8.6 [+1.4, +17.1]; c02_nb_L15u1047_k2_vs_baseline es +8.6 [+1.4, +17.1]; c02_nb_L15u1047_k2_vs_baseline it +11.4 [+2.9, +21.4]; c02_nb_L15u1047_k2_vs_baseline ja +15.9 [+7.1, +25.7]; c02_nb_L15u1047_k2_vs_baseline ko +17.1 [+8.6, +27.1]; c02_nb_L15u1047_k2_vs_baseline pt +11.7 [+0.1, +23.3]; c02_nb_L15u1047_k2_vs_baseline ru +5.7 [+1.4, +11.4]; c02_nb_L15u1047_k2_vs_baseline tr +11.4 [+4.3, +18.6]; c02_nb_L15u1047_k2_vs_baseline vi +10.0 [+2.9, +17.1]; c02_nb_L15u1047_k2_vs_recover es -5.7 [-11.4, -1.4]; c02_nb_L15u1047_k2_vs_instr_end de +8.6 [+1.4, +17.1]; c02_nb_L15u1047_k2_vs_instr_end ja +14.2 [+6.8, +22.8]; c02_nb_L15u1047_k2_vs_instr_end ru +4.4 [+0.1, +10.0]; c02_nb_L15u1047_k2_vs_instr_end tr +13.0 [+5.7, +21.4]; c02_nb_L15u1047_k2_vs_instr_end zh +11.8 [+1.7, +22.8]; h5_a2_n5_vs_baseline ja +13.0 [+4.3, +22.1]; h5_a2_n5_vs_baseline ko +12.6 [+4.1, +21.4]; h5_a2_n5_vs_recover ar -7.2 [-14.3, -1.4]; h5_a2_n5_vs_recover es -11.4 [-20.0, -4.3]; h5_a2_n5_vs_recover fr -10.0 [-18.6, -1.4]; h5_a2_n5_vs_recover it -8.6 [-15.7, -2.9]; h5_a2_n5_vs_recover ru -14.3 [-22.9, -7.1]; h5_a2_n5_vs_instr_end ja +11.3 [+2.5, +21.3]; h5_a2_n5_vs_instr_end vi -5.7 [-11.4, -1.4]; mix21_22b0.75_23b0.5_vs_baseline hi +8.5 [+1.3, +17.1]; mix21_22b0.75_23b0.5_vs_baseline ja +10.4 [+0.6, +20.4]; mix21_22b0.75_23b0.5_vs_baseline ko +14.1 [+5.5, +23.9]; mix21_22b0.75_23b0.5_vs_baseline ru +8.6 [+2.9, +15.7]; mix21_22b0.75_23b0.5_vs_recover es -10.0 [-17.1, -4.3]; mix21_22b0.75_23b0.5_vs_recover tr -9.9 [-17.1, -3.9]; mix21_22b0.75_23b0.5_vs_recover vi -7.1 [-14.3, -1.4]; mix21_22b0.75_23b0.5_vs_instr_end hi +12.8 [+4.2, +22.6]; mix21_22b0.75_23b0.5_vs_instr_end ru +7.3 [+1.5, +14.3]; combo_a14_b14_vs_baseline ko +17.1 [+8.6, +27.1]; combo_a14_b14_vs_baseline pt +8.9 [+1.4, +16.9]; combo_a14_b14_vs_baseline vi +8.6 [+1.4, +17.1]; combo_a14_b14_vs_recover es -10.0 [-17.1, -4.3]; combo_a14_b14_vs_recover it -8.6 [-15.7, -2.9]; combo_a14_b14_vs_recover ja -7.0 [-14.1, -1.3]; combo_a14_b14_vs_recover ru -8.7 [-15.9, -2.9]; combo_a14_b14_vs_instr_end hi +11.4 [+4.3, +20.0]; combo_a14_b14_vs_instr_end ko +7.3 [+0.1, +14.7]

guard vs baseline (baseline loop % 1.94, mean NLL 0.723):

| method | loop % (change) | mean NLL (change) | empty % | guard | source |
|---|---|---|---|---|---|
| c02_nb_L15u1047_k2 | 2.65 (+0.71) | 0.857 (+0.134) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/08/c02_nb_L15u1047_k2.guard.json` |
| h5_a2_n5 | 2.55 (+0.61) | 0.856 (+0.133) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/08/h5_a2_n5.guard.json` |
| mix21_22b0.75_23b0.5 | 4.39 (+2.45) | 0.784 (+0.062) | 0.0 | fail loop_pts | `runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/08/mix21_22b0.75_23b0.5.guard.json` |
| combo_a14_b14 | 3.37 (+1.43) | 0.800 (+0.077) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/08/combo_a14_b14.guard.json` |
| recover | 1.94 (+0.00) | 0.880 (+0.157) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/08/recover.guard.json` |
| instr_end | 2.24 (+0.31) | 0.750 (+0.028) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/08/instr_end.guard.json` |

## 08 lcb-greedy (`runs/2026-11-22-partc-run/scores/08/lcb-greedy/stats.json`, rows 714, clusters 17)

| method | lpr drop | lpr fail | lpr pass | full % drop | wpr | late switch % | loop % | cap % | unscored (count of scored=0 in perrow) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 62.3 | 59.8 | 63.9 | 29.05 | 87.3 | 8.2 | 9.52 | 89.2 | 29 of 714 |
| c02_nb_L15u1047_k2 | 92.2 | 86.1 | 92.4 | 3.14 | 79.0 | 3.9 | 9.52 | 88.9 | 45 of 714 |
| h5_a2_n5 | 81.9 | 76.2 | 83.2 | 7.53 | 80.5 | 8.4 | 8.68 | 85.7 | 50 of 714 |
| mix21_22b0.75_23b0.5 | 80.8 | 79.1 | 81.2 | 11.30 | 81.3 | 7.6 | 10.64 | 89.8 | 15 of 714 |
| combo_a14_b14 | 79.9 | 76.9 | 80.5 | 11.19 | 79.7 | 8.3 | 10.22 | 92.3 | 26 of 714 |
| recover | 93.5 | 88.7 | 93.7 | 0.74 | 88.1 | 5.3 | 9.24 | 90.1 | 36 of 714 |
| instr_end | 76.9 | 73.7 | 78.0 | 12.88 | 82.3 | 9.5 | 6.44 | 87.8 | 31 of 714 |

| a vs b | lpr drop | lpr fail | lpr pass | full % drop | loop % drop | mcnemar a better / b better, p |
|---|---|---|---|---|---|---|
| recover_vs_baseline | +31.2 [+19.2, +43.7] p 0.0003 | +28.9 [+18.6, +39.5] p 0.0003 | +29.8 [+18.2, +42.2] p 0.0005 | -28.3 [-40.9, -16.9] p 0.0003 | -0.3 [-5.0, +3.5] p 0.9637 | 209 / 14, 0.0000 |
| instr_end_vs_baseline | +14.7 [+8.8, +21.4] p 0.0005 | +13.9 [+8.7, +19.6] p 0.0003 | +14.1 [+8.3, +20.9] p 0.0005 | -16.2 [-24.2, -8.6] p 0.0007 | -3.1 [-8.7, +0.4] p 0.2820 | 110 / 16, 0.0000 |
| c02_nb_L15u1047_k2_vs_baseline | +29.9 [+19.2, +41.4] p 0.0003 | +26.3 [+16.2, +37.5] p 0.0003 | +28.6 [+18.1, +39.9] p 0.0003 | -25.9 [-37.9, -15.3] p 0.0003 | +0.0 [-4.9, +4.1] p 1.0000 | 190 / 10, 0.0000 |
| c02_nb_L15u1047_k2_vs_recover | -1.3 [-5.7, +2.3] p 0.5864 | -2.5 [-8.0, +1.7] p 0.4594 | -1.3 [-5.3, +2.2] p 0.6174 | +2.4 [+0.4, +4.9] p 0.0490 | +0.3 [-3.9, +4.1] p 0.9532 | 32 / 41, 0.3492 |
| c02_nb_L15u1047_k2_vs_instr_end | +15.2 [+7.1, +23.6] p 0.0039 | +12.5 [+4.1, +20.7] p 0.0122 | +14.4 [+6.6, +22.5] p 0.0040 | -9.7 [-17.5, -3.3] p 0.0131 | +3.1 [+0.7, +5.5] p 0.0368 | 114 / 20, 0.0000 |
| h5_a2_n5_vs_baseline | +19.6 [+11.6, +28.2] p 0.0009 | +16.4 [+7.8, +25.8] p 0.0034 | +19.3 [+11.6, +27.7] p 0.0005 | -21.5 [-30.4, -13.1] p 0.0006 | -0.8 [-6.7, +4.1] p 0.8504 | 150 / 30, 0.0000 |
| h5_a2_n5_vs_recover | -11.6 [-19.3, -5.1] p 0.0006 | -12.5 [-18.8, -6.9] p 0.0003 | -10.5 [-17.6, -4.5] p 0.0033 | +6.8 [+2.2, +13.1] p 0.0009 | -0.6 [-3.4, +2.2] p 0.7754 | 21 / 94, 0.0000 |
| h5_a2_n5_vs_instr_end | +5.0 [-0.8, +10.7] p 0.1245 | +2.5 [-3.8, +8.7] p 0.4847 | +5.2 [+0.0, +10.6] p 0.0910 | -5.4 [-11.1, +0.3] p 0.1033 | +2.2 [-1.7, +6.3] p 0.3304 | 86 / 56, 0.0147 |
| mix21_22b0.75_23b0.5_vs_baseline | +18.6 [+11.0, +26.7] p 0.0003 | +19.3 [+12.0, +27.3] p 0.0003 | +17.4 [+9.9, +25.5] p 0.0006 | -17.7 [-25.7, -10.4] p 0.0006 | +1.1 [-4.6, +5.9] p 0.7455 | 135 / 10, 0.0000 |
| mix21_22b0.75_23b0.5_vs_recover | -12.6 [-21.2, -5.5] p 0.0011 | -9.5 [-16.4, -3.5] p 0.0095 | -12.5 [-20.6, -5.6] p 0.0011 | +10.6 [+4.0, +19.3] p 0.0003 | +1.4 [-0.6, +3.4] p 0.2475 | 22 / 99, 0.0000 |
| mix21_22b0.75_23b0.5_vs_instr_end | +3.9 [-3.7, +9.9] p 0.3042 | +5.5 [-1.3, +10.9] p 0.1200 | +3.2 [-4.1, +9.2] p 0.4198 | -1.6 [-8.4, +6.4] p 0.7024 | +4.2 [+1.0, +8.0] p 0.0288 | 89 / 58, 0.0131 |
| combo_a14_b14_vs_baseline | +17.6 [+10.1, +26.1] p 0.0003 | +17.1 [+9.7, +25.5] p 0.0003 | +16.7 [+9.2, +25.2] p 0.0005 | -17.9 [-25.9, -10.8] p 0.0003 | +0.7 [-4.2, +4.9] p 0.8339 | 134 / 22, 0.0000 |
| combo_a14_b14_vs_recover | -13.6 [-22.3, -6.3] p 0.0008 | -11.8 [-19.0, -5.5] p 0.0015 | -13.2 [-21.3, -6.2] p 0.0014 | +10.5 [+4.1, +18.7] p 0.0006 | +1.0 [-1.8, +3.8] p 0.5774 | 20 / 104, 0.0000 |
| combo_a14_b14_vs_instr_end | +2.9 [-4.5, +9.2] p 0.4458 | +3.2 [-3.6, +9.1] p 0.3899 | +2.5 [-4.6, +8.7] p 0.5224 | -1.7 [-8.1, +5.7] p 0.6530 | +3.8 [+0.1, +7.7] p 0.0827 | 85 / 65, 0.1205 |

per-language cells with a CI that excludes 0 (drop rule): recover_vs_baseline ar +29.0 [+11.1, +47.7]; recover_vs_baseline de +29.3 [+8.5, +50.0]; recover_vs_baseline es +25.9 [+8.3, +43.8]; recover_vs_baseline fr +33.3 [+17.6, +50.9]; recover_vs_baseline hi +40.8 [+21.6, +60.7]; recover_vs_baseline it +33.9 [+19.6, +49.3]; recover_vs_baseline ja +31.4 [+16.0, +48.6]; recover_vs_baseline ko +48.8 [+29.4, +68.1]; recover_vs_baseline pt +27.0 [+12.0, +44.3]; recover_vs_baseline ru +34.4 [+16.3, +53.8]; recover_vs_baseline tr +37.7 [+19.4, +56.9]; recover_vs_baseline vi +29.9 [+12.0, +48.9]; recover_vs_baseline zh +25.2 [+11.3, +40.9]; instr_end_vs_baseline ar +12.1 [+2.0, +23.1]; instr_end_vs_baseline de +11.3 [+0.6, +23.0]; instr_end_vs_baseline es +13.7 [+3.9, +25.2]; instr_end_vs_baseline fr +13.3 [+2.0, +25.3]; instr_end_vs_baseline it +22.0 [+11.8, +33.3]; instr_end_vs_baseline ja +10.9 [+0.6, +20.7]; instr_end_vs_baseline pt +17.0 [+7.8, +28.0]; instr_end_vs_baseline ru +19.2 [+5.5, +33.2]; instr_end_vs_baseline tr +22.9 [+11.3, +35.6]; instr_end_vs_baseline vi +18.0 [+5.9, +32.0]; instr_end_vs_baseline zh +13.7 [+3.9, +23.5]; c02_nb_L15u1047_k2_vs_baseline ar +24.7 [+11.3, +40.1]; c02_nb_L15u1047_k2_vs_baseline de +31.2 [+14.5, +49.0]; c02_nb_L15u1047_k2_vs_baseline es +23.9 [+8.0, +41.2]; c02_nb_L15u1047_k2_vs_baseline fr +31.2 [+13.6, +50.8]; c02_nb_L15u1047_k2_vs_baseline hi +34.7 [+16.5, +54.3]; c02_nb_L15u1047_k2_vs_baseline id +30.2 [+15.7, +45.2]; c02_nb_L15u1047_k2_vs_baseline it +35.9 [+19.6, +52.9]; c02_nb_L15u1047_k2_vs_baseline ja +21.4 [+0.4, +39.9]; c02_nb_L15u1047_k2_vs_baseline ko +46.2 [+27.5, +65.6]; c02_nb_L15u1047_k2_vs_baseline pt +18.8 [+6.1, +34.1]; c02_nb_L15u1047_k2_vs_baseline ru +36.6 [+18.3, +56.0]; c02_nb_L15u1047_k2_vs_baseline tr +47.9 [+27.5, +68.8]; c02_nb_L15u1047_k2_vs_baseline vi +32.0 [+15.7, +49.0]; c02_nb_L15u1047_k2_vs_recover id +19.6 [+3.9, +33.3]; c02_nb_L15u1047_k2_vs_recover zh -21.3 [-42.8, -1.5]; c02_nb_L15u1047_k2_vs_instr_end de +19.9 [+6.1, +35.3]; c02_nb_L15u1047_k2_vs_instr_end fr +17.9 [+1.9, +37.2]; c02_nb_L15u1047_k2_vs_instr_end hi +23.3 [+7.8, +42.1]; c02_nb_L15u1047_k2_vs_instr_end id +22.8 [+9.8, +37.5]; c02_nb_L15u1047_k2_vs_instr_end it +13.9 [+1.9, +27.5]; c02_nb_L15u1047_k2_vs_instr_end ko +33.5 [+16.6, +52.1]; c02_nb_L15u1047_k2_vs_instr_end ru +17.4 [+6.3, +31.1]; c02_nb_L15u1047_k2_vs_instr_end tr +25.0 [+8.5, +43.8]; c02_nb_L15u1047_k2_vs_instr_end vi +14.0 [+4.0, +26.0]; h5_a2_n5_vs_baseline ar +20.1 [+9.1, +32.6]; h5_a2_n5_vs_baseline de +21.6 [+2.8, +40.8]; h5_a2_n5_vs_baseline fr +26.8 [+9.6, +44.3]; h5_a2_n5_vs_baseline hi +27.3 [+10.1, +45.9]; h5_a2_n5_vs_baseline it +29.8 [+13.7, +47.0]; h5_a2_n5_vs_baseline ko +31.9 [+11.9, +51.7]; h5_a2_n5_vs_baseline ru +19.6 [+1.3, +39.6]; h5_a2_n5_vs_baseline tr +29.3 [+11.8, +47.9]; h5_a2_n5_vs_baseline zh +11.2 [+1.4, +20.9]; h5_a2_n5_vs_recover de -7.8 [-14.4, -1.6]; h5_a2_n5_vs_recover es -12.2 [-26.5, -2.0]; h5_a2_n5_vs_recover hi -13.5 [-29.2, -0.3]; h5_a2_n5_vs_recover ja -23.7 [-39.5, -9.9]; h5_a2_n5_vs_recover ko -16.9 [-31.6, -5.7]; h5_a2_n5_vs_recover pt -17.0 [-32.3, -6.0]; h5_a2_n5_vs_recover tr -8.4 [-19.3, -0.7]; h5_a2_n5_vs_recover vi -15.9 [-31.9, -2.0]; mix21_22b0.75_23b0.5_vs_baseline ar +25.0 [+11.8, +40.5]; mix21_22b0.75_23b0.5_vs_baseline de +19.3 [+6.8, +34.4]; mix21_22b0.75_23b0.5_vs_baseline es +18.2 [+4.7, +32.2]; mix21_22b0.75_23b0.5_vs_baseline fr +15.3 [+3.9, +29.4]; mix21_22b0.75_23b0.5_vs_baseline hi +31.0 [+9.6, +51.0]; mix21_22b0.75_23b0.5_vs_baseline id +14.0 [+5.9, +24.5]; mix21_22b0.75_23b0.5_vs_baseline it +24.3 [+11.8, +38.2]; mix21_22b0.75_23b0.5_vs_baseline ko +41.3 [+24.0, +58.8]; mix21_22b0.75_23b0.5_vs_baseline ru +22.8 [+10.2, +37.8]; mix21_22b0.75_23b0.5_vs_baseline tr +20.8 [+8.9, +34.5]; mix21_22b0.75_23b0.5_vs_recover fr -18.0 [-32.0, -4.2]; mix21_22b0.75_23b0.5_vs_recover it -9.6 [-19.6, -2.0]; mix21_22b0.75_23b0.5_vs_recover ja -24.0 [-42.0, -7.8]; mix21_22b0.75_23b0.5_vs_recover pt -17.7 [-29.6, -7.7]; mix21_22b0.75_23b0.5_vs_recover tr -16.9 [-31.7, -2.7]; mix21_22b0.75_23b0.5_vs_recover vi -20.4 [-36.2, -6.2]; mix21_22b0.75_23b0.5_vs_recover zh -23.3 [-38.7, -7.8]; mix21_22b0.75_23b0.5_vs_instr_end ko +28.6 [+12.2, +45.1]; combo_a14_b14_vs_baseline ar +18.8 [+8.3, +31.2]; combo_a14_b14_vs_baseline es +15.8 [+4.0, +29.3]; combo_a14_b14_vs_baseline hi +32.7 [+16.9, +50.2]; combo_a14_b14_vs_baseline it +24.0 [+10.4, +39.6]; combo_a14_b14_vs_baseline ja +12.5 [+2.5, +21.9]; combo_a14_b14_vs_baseline ko +34.9 [+17.9, +53.8]; combo_a14_b14_vs_baseline pt +14.9 [+2.0, +30.1]; combo_a14_b14_vs_baseline ru +19.6 [+8.7, +31.5]; combo_a14_b14_vs_baseline tr +35.2 [+18.5, +53.0]; combo_a14_b14_vs_baseline vi +18.3 [+2.6, +35.3]; combo_a14_b14_vs_recover de -21.0 [-37.3, -6.1]; combo_a14_b14_vs_recover fr -21.5 [-35.2, -9.8]; combo_a14_b14_vs_recover ja -18.9 [-31.2, -6.8]; combo_a14_b14_vs_recover pt -12.1 [-26.2, -2.0]; combo_a14_b14_vs_recover ru -14.8 [-27.8, -3.5]; combo_a14_b14_vs_recover zh -29.1 [-47.1, -11.8]; combo_a14_b14_vs_instr_end hi +21.3 [+3.3, +42.4]; combo_a14_b14_vs_instr_end ko +22.1 [+6.2, +40.0]; combo_a14_b14_vs_instr_end zh -17.6 [-29.4, -5.9]

## 08 lcb-long (`runs/2026-11-22-partc-run/scores/08/lcb-long/stats.json`, rows 238, clusters 17)

| method | lpr drop | lpr fail | lpr pass | full % drop | wpr | late switch % | loop % | cap % | unscored (count of scored=0 in perrow) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 62.5 | 60.1 | 63.9 | 25.76 | 86.3 | 10.9 | 21.01 | 41.6 | 9 of 238 |
| c02_nb_L15u1047_k2 | 90.0 | 85.7 | 90.3 | 1.76 | 79.3 | 7.0 | 34.45 | 52.1 | 11 of 238 |
| h5_a2_n5 | 83.6 | 77.7 | 84.9 | 8.60 | 84.4 | 6.3 | 22.27 | 40.3 | 17 of 238 |
| mix21_22b0.75_23b0.5 | 77.2 | 75.2 | 77.7 | 10.78 | 75.9 | 11.6 | 28.15 | 46.2 | 6 of 238 |
| combo_a14_b14 | 80.6 | 78.6 | 81.1 | 8.62 | 77.0 | 9.5 | 30.67 | 50.0 | 6 of 238 |
| recover | 92.6 | 84.9 | 92.9 | 0.46 | 85.9 | 7.3 | 31.09 | 53.4 | 19 of 238 |
| instr_end | 75.2 | 72.3 | 76.1 | 12.23 | 80.1 | 12.7 | 24.37 | 45.8 | 9 of 238 |

| a vs b | lpr drop | lpr fail | lpr pass | full % drop | loop % drop | mcnemar a better / b better, p |
|---|---|---|---|---|---|---|
| recover_vs_baseline | +30.1 [+18.1, +42.9] p 0.0002 | +24.8 [+15.5, +34.9] p 0.0002 | +29.0 [+17.2, +42.0] p 0.0004 | -25.3 [-37.8, -14.5] p 0.0003 | +10.1 [+3.8, +16.4] p 0.0115 | 63 / 2, 0.0000 |
| instr_end_vs_baseline | +12.7 [+5.3, +20.4] p 0.0047 | +12.2 [+5.9, +18.9] p 0.0045 | +12.2 [+5.0, +19.7] p 0.0084 | -13.5 [-22.2, -5.1] p 0.0090 | +3.4 [+0.4, +6.3] p 0.0739 | 32 / 5, 0.0000 |
| c02_nb_L15u1047_k2_vs_baseline | +27.4 [+16.3, +39.5] p 0.0002 | +25.6 [+15.1, +36.6] p 0.0002 | +26.5 [+15.5, +38.7] p 0.0005 | -24.0 [-35.9, -13.6] p 0.0004 | +13.4 [+5.9, +21.0] p 0.0051 | 64 / 4, 0.0000 |
| c02_nb_L15u1047_k2_vs_recover | -2.6 [-6.6, +0.9] p 0.2263 | +0.8 [-4.6, +6.3] p 0.8856 | -2.5 [-5.9, +0.8] p 0.2795 | +1.3 [-0.5, +3.1] p 0.3722 | +3.4 [-3.4, +10.1] p 0.4116 | 8 / 13, 0.3833 |
| c02_nb_L15u1047_k2_vs_instr_end | +14.8 [+7.0, +23.5] p 0.0033 | +13.4 [+6.3, +21.0] p 0.0043 | +14.3 [+6.7, +23.1] p 0.0036 | -10.5 [-16.6, -4.9] p 0.0043 | +10.1 [+3.4, +16.8] p 0.0172 | 42 / 10, 0.0000 |
| h5_a2_n5_vs_baseline | +21.0 [+11.5, +31.1] p 0.0012 | +17.6 [+8.8, +27.3] p 0.0035 | +21.0 [+11.3, +31.1] p 0.0012 | -17.2 [-26.5, -8.9] p 0.0005 | +1.3 [-7.6, +9.7] p 0.8550 | 52 / 8, 0.0000 |
| h5_a2_n5_vs_recover | -9.0 [-17.2, -2.4] p 0.0236 | -7.1 [-12.6, -1.7] p 0.0383 | -8.0 [-15.5, -1.7] p 0.0461 | +8.1 [+1.8, +17.0] p 0.0187 | -8.8 [-15.5, -2.5] p 0.0240 | 5 / 22, 0.0015 |
| h5_a2_n5_vs_instr_end | +8.4 [+0.7, +16.9] p 0.0617 | +5.5 [-1.7, +13.0] p 0.2217 | +8.8 [+1.7, +17.2] p 0.0510 | -3.6 [-10.4, +3.2] p 0.3190 | -2.1 [-10.9, +5.9] p 0.7099 | 32 / 17, 0.0444 |
| mix21_22b0.75_23b0.5_vs_baseline | +14.6 [+7.9, +21.3] p 0.0009 | +15.1 [+8.8, +21.4] p 0.0010 | +13.9 [+7.1, +20.6] p 0.0027 | -15.0 [-22.4, -8.2] p 0.0006 | +7.1 [+2.5, +12.2] p 0.0160 | 39 / 7, 0.0000 |
| mix21_22b0.75_23b0.5_vs_recover | -15.4 [-24.8, -6.9] p 0.0036 | -9.7 [-18.1, -2.1] p 0.0420 | -15.1 [-24.4, -6.7] p 0.0044 | +10.3 [+4.2, +18.4] p 0.0015 | -2.9 [-9.7, +3.8] p 0.4923 | 6 / 38, 0.0000 |
| mix21_22b0.75_23b0.5_vs_instr_end | +2.0 [-3.2, +6.8] p 0.4550 | +2.9 [-2.1, +7.6] p 0.3224 | +1.7 [-3.4, +6.3] p 0.6386 | -1.5 [-7.9, +4.6] p 0.6558 | +3.8 [-0.8, +8.4] p 0.2010 | 27 / 22, 0.5682 |
| combo_a14_b14_vs_baseline | +18.0 [+9.9, +26.5] p 0.0010 | +18.5 [+10.1, +26.5] p 0.0016 | +17.2 [+9.7, +25.2] p 0.0015 | -17.1 [-26.4, -8.7] p 0.0010 | +9.7 [+4.6, +15.1] p 0.0020 | 43 / 6, 0.0000 |
| combo_a14_b14_vs_recover | -12.0 [-19.9, -5.3] p 0.0049 | -6.3 [-14.7, +1.3] p 0.1915 | -11.8 [-19.7, -5.0] p 0.0075 | +8.2 [+3.0, +14.0] p 0.0139 | -0.4 [-5.0, +3.8] p 1.0000 | 8 / 34, 0.0001 |
| combo_a14_b14_vs_instr_end | +5.4 [+0.9, +10.1] p 0.0387 | +6.3 [+1.3, +12.2] p 0.0611 | +5.0 [+0.8, +9.7] p 0.0657 | -3.6 [-7.9, +1.1] p 0.1649 | +6.3 [+1.7, +11.3] p 0.0430 | 28 / 17, 0.1352 |

per-language cells with a CI that excludes 0 (drop rule): recover_vs_baseline ar +37.5 [+14.3, +62.5]; recover_vs_baseline de +41.2 [+17.6, +64.7]; recover_vs_baseline hi +37.9 [+14.3, +62.5]; recover_vs_baseline ko +37.5 [+14.2, +62.5]; recover_vs_baseline pt +42.9 [+17.9, +68.8]; recover_vs_baseline ru +25.0 [+6.2, +47.1]; recover_vs_baseline tr +43.3 [+18.8, +68.8]; recover_vs_baseline vi +29.4 [+11.8, +52.9]; recover_vs_baseline zh +58.8 [+35.3, +82.4]; instr_end_vs_baseline pt +25.0 [+1.8, +48.8]; c02_nb_L15u1047_k2_vs_baseline ar +31.6 [+11.8, +54.9]; c02_nb_L15u1047_k2_vs_baseline de +41.2 [+17.6, +64.7]; c02_nb_L15u1047_k2_vs_baseline fr +23.5 [+5.9, +47.1]; c02_nb_L15u1047_k2_vs_baseline hi +32.0 [+3.1, +58.8]; c02_nb_L15u1047_k2_vs_baseline it +25.0 [+6.2, +47.1]; c02_nb_L15u1047_k2_vs_baseline ko +43.8 [+20.0, +68.8]; c02_nb_L15u1047_k2_vs_baseline pt +28.6 [+6.2, +52.9]; c02_nb_L15u1047_k2_vs_baseline ru +25.0 [+6.2, +47.1]; c02_nb_L15u1047_k2_vs_baseline tr +42.9 [+18.8, +68.1]; c02_nb_L15u1047_k2_vs_baseline vi +29.4 [+11.8, +52.9]; c02_nb_L15u1047_k2_vs_baseline zh +35.3 [+11.8, +58.8]; c02_nb_L15u1047_k2_vs_recover zh -23.5 [-47.1, -5.9]; c02_nb_L15u1047_k2_vs_instr_end de +25.0 [+6.2, +47.1]; c02_nb_L15u1047_k2_vs_instr_end ko +31.2 [+11.8, +56.2]; h5_a2_n5_vs_baseline de +35.3 [+11.8, +58.8]; h5_a2_n5_vs_baseline pt +30.0 [+9.9, +53.3]; h5_a2_n5_vs_baseline tr +25.0 [+5.9, +47.1]; h5_a2_n5_vs_baseline vi +23.2 [+5.1, +44.6]; h5_a2_n5_vs_baseline zh +46.0 [+23.5, +70.2]; h5_a2_n5_vs_recover ar -28.6 [-53.8, -7.1]; h5_a2_n5_vs_instr_end zh +22.4 [+5.9, +43.3]; mix21_22b0.75_23b0.5_vs_baseline ar +25.7 [+5.9, +47.5]; mix21_22b0.75_23b0.5_vs_baseline de +23.5 [+5.9, +47.1]; mix21_22b0.75_23b0.5_vs_baseline hi +31.2 [+11.0, +55.0]; mix21_22b0.75_23b0.5_vs_baseline pt +20.6 [+3.1, +41.2]; mix21_22b0.75_23b0.5_vs_baseline tr +38.2 [+15.7, +62.9]; mix21_22b0.75_23b0.5_vs_recover ja -25.0 [-47.1, -6.2]; mix21_22b0.75_23b0.5_vs_recover vi -26.7 [-50.0, -6.2]; mix21_22b0.75_23b0.5_vs_recover zh -52.9 [-76.5, -29.4]; mix21_22b0.75_23b0.5_vs_instr_end hi +18.8 [+0.4, +40.0]; mix21_22b0.75_23b0.5_vs_instr_end tr +23.5 [+5.9, +47.1]; combo_a14_b14_vs_baseline ar +19.9 [+1.8, +41.2]; combo_a14_b14_vs_baseline de +22.4 [+5.9, +44.5]; combo_a14_b14_vs_baseline hi +37.5 [+14.3, +62.5]; combo_a14_b14_vs_baseline it +25.0 [+6.2, +47.1]; combo_a14_b14_vs_baseline ko +26.1 [+5.9, +47.9]; combo_a14_b14_vs_baseline pt +32.4 [+11.8, +56.5]; combo_a14_b14_vs_baseline tr +31.2 [+10.9, +55.0]; combo_a14_b14_vs_recover zh -41.2 [-64.7, -17.6]; combo_a14_b14_vs_instr_end hi +25.0 [+6.2, +47.1]

long400 answers that start with the 100-token row (`starts_with_old`): baseline 235 of 238; c02_nb_L15u1047_k2 237 of 238; h5_a2_n5 238 of 238; mix21_22b0.75_23b0.5 236 of 238; combo_a14_b14 236 of 238; recover 237 of 238; instr_end 237 of 238

## 08 greedy minus seed 1 sampled (`runs/2026-11-22-partc-run/scores/08/lcb-greedy/stats_greedy_vs_s1.json`)

| comparison | lpr drop | full % drop |
|---|---|---|
| baseline_greedy_vs_baseline_s1 | -0.6 [-2.1, +0.9] p 0.4405 | +0.5 [-1.1, +1.9] p 0.5275 |
| c02_nb_L15u1047_k2_greedy_vs_c02_nb_L15u1047_k2_s1 | -0.9 [-2.9, +0.9] p 0.4428 | +1.2 [+0.3, +2.3] p 0.0448 |
| h5_a2_n5_greedy_vs_h5_a2_n5_s1 | -1.5 [-4.0, +0.9] p 0.2819 | +0.5 [-1.3, +2.0] p 0.5970 |
| mix21_22b0.75_23b0.5_greedy_vs_mix21_22b0.75_23b0.5_s1 | -2.0 [-3.2, -0.8] p 0.0074 | +1.0 [+0.1, +1.8] p 0.0782 |
| combo_a14_b14_greedy_vs_combo_a14_b14_s1 | -1.0 [-3.0, +0.9] p 0.3242 | +0.8 [-0.9, +2.8] p 0.4811 |
| recover_greedy_vs_recover_s1 | -1.3 [-3.8, +0.7] p 0.3479 | +0.1 [-0.0, +0.4] p 0.9358 |
| instr_end_greedy_vs_instr_end_s1 | -0.6 [-2.5, +1.4] p 0.5426 | +0.2 [-0.8, +1.1] p 0.6758 |

## 08 global-mmlu (`runs/2026-11-22-partc-run/scores/08/global-mmlu/stats.json`, rows 1400, clusters 100)

- observed baseline: acc 40.00, acc_ar 39.00, acc_de 34.00, acc_es 48.00, acc_fr 39.00, acc_hi 34.00, acc_id 40.00, acc_it 40.00, acc_ja 39.00, acc_ko 40.00, acc_pt 41.00, acc_ru 37.00, acc_tr 37.00, acc_vi 46.00, acc_zh 46.00, acc_group_Humanities 29.83, acc_group_STEM 38.96, acc_group_Social Sciences 61.36, acc_group_Medical 37.66, acc_group_Other 30.95, acc_group_Business 35.71, acc_CS 50.00, acc_CA 56.59
- observed c02_nb_L15u1047_k2: acc 40.43, acc_ar 40.00, acc_de 34.00, acc_es 48.00, acc_fr 40.00, acc_hi 35.00, acc_id 39.00, acc_it 41.00, acc_ja 43.00, acc_ko 42.00, acc_pt 42.00, acc_ru 34.00, acc_tr 37.00, acc_vi 45.00, acc_zh 46.00, acc_group_Humanities 31.09, acc_group_STEM 39.29, acc_group_Social Sciences 57.47, acc_group_Medical 37.66, acc_group_Other 32.14, acc_group_Business 50.00, acc_CS 42.86, acc_CA 55.49
- observed h5_a2_n5: acc 40.14, acc_ar 42.00, acc_de 34.00, acc_es 45.00, acc_fr 42.00, acc_hi 39.00, acc_id 43.00, acc_it 42.00, acc_ja 43.00, acc_ko 38.00, acc_pt 40.00, acc_ru 36.00, acc_tr 35.00, acc_vi 44.00, acc_zh 39.00, acc_group_Humanities 28.99, acc_group_STEM 35.71, acc_group_Social Sciences 63.31, acc_group_Medical 41.56, acc_group_Other 27.38, acc_group_Business 45.71, acc_CS 40.00, acc_CA 55.49
- observed mix21_22b0.75_23b0.5: acc 38.79, acc_ar 37.00, acc_de 33.00, acc_es 47.00, acc_fr 39.00, acc_hi 36.00, acc_id 38.00, acc_it 41.00, acc_ja 40.00, acc_ko 34.00, acc_pt 41.00, acc_ru 33.00, acc_tr 33.00, acc_vi 48.00, acc_zh 43.00, acc_group_Humanities 31.09, acc_group_STEM 38.64, acc_group_Social Sciences 56.17, acc_group_Medical 36.36, acc_group_Other 32.14, acc_group_Business 28.57, acc_CS 48.57, acc_CA 54.95
- observed combo_a14_b14: acc 39.93, acc_ar 38.00, acc_de 31.00, acc_es 49.00, acc_fr 39.00, acc_hi 34.00, acc_id 40.00, acc_it 41.00, acc_ja 39.00, acc_ko 39.00, acc_pt 44.00, acc_ru 36.00, acc_tr 38.00, acc_vi 46.00, acc_zh 45.00, acc_group_Humanities 29.41, acc_group_STEM 38.64, acc_group_Social Sciences 61.69, acc_group_Medical 37.01, acc_group_Other 32.14, acc_group_Business 37.14, acc_CS 48.57, acc_CA 56.04

### c02_nb_L15u1047_k2_vs_baseline: no damage shown, more than 2 points ruled out: False
- mcnemar: a better 49, b better 43, p 0.6024, pairs 1400
- language leads: []
- acc: a 40.43, b 40.00, +0.4 [-1.4, +2.3] p 0.7099
- acc_ar: a 40.00, b 39.00, +1.0 [-3.0, +6.0] p 1.0000
- acc_de: a 34.00, b 34.00, +0.0 [-5.0, +5.0] p 1.0000
- acc_es: a 48.00, b 48.00, +0.0 [-6.0, +6.0] p 1.0000
- acc_fr: a 40.00, b 39.00, +1.0 [-3.0, +5.0] p 1.0000
- acc_hi: a 35.00, b 34.00, +1.0 [-4.0, +6.0] p 1.0000
- acc_id: a 39.00, b 40.00, -1.0 [-7.0, +5.0] p 1.0000
- acc_it: a 41.00, b 40.00, +1.0 [-3.0, +5.0] p 1.0000
- acc_ja: a 43.00, b 39.00, +4.0 [-1.0, +9.0] p 0.2174
- acc_ko: a 42.00, b 40.00, +2.0 [-3.0, +7.0] p 0.6835
- acc_pt: a 42.00, b 41.00, +1.0 [-3.0, +5.0] p 1.0000
- acc_ru: a 34.00, b 37.00, -3.0 [-7.0, +0.0] p 0.2540
- acc_tr: a 37.00, b 37.00, +0.0 [-6.0, +5.0] p 1.0000
- acc_vi: a 45.00, b 46.00, -1.0 [-5.0, +3.0] p 1.0000
- acc_zh: a 46.00, b 46.00, +0.0 [-6.0, +6.0] p 1.0000
- acc_group_Humanities: a 31.09, b 29.83, +1.3 [-1.7, +4.4] p 0.5143
- acc_group_STEM: a 39.29, b 38.96, +0.3 [-2.6, +3.1] p 1.0000
- acc_group_Social Sciences: a 57.47, b 61.36, -3.9 [-7.1, -0.7] p 0.0529
- acc_group_Medical: a 37.66, b 37.66, +0.0 [-1.9, +1.9] p 1.0000
- acc_group_Other: a 32.14, b 30.95, +1.2 [+0.0, +3.6] p 1.0000
- acc_group_Business: a 50.00, b 35.71, +14.3 [-7.1, +35.7] p 0.3113
- acc_CS: a 42.86, b 50.00, -7.1 [-15.7, +0.0] p 0.2457
- acc_CA: a 55.49, b 56.59, -1.1 [-4.4, +1.8] p 0.7523

### h5_a2_n5_vs_baseline: no damage shown, more than 2 points ruled out: False
- mcnemar: a better 95, b better 93, p 0.9419, pairs 1400
- language leads: []
- acc: a 40.14, b 40.00, +0.1 [-3.4, +3.8] p 0.9694
- acc_ar: a 42.00, b 39.00, +3.0 [-5.0, +11.0] p 0.6235
- acc_de: a 34.00, b 34.00, +0.0 [-7.0, +7.0] p 1.0000
- acc_es: a 45.00, b 48.00, -3.0 [-9.0, +3.0] p 0.5134
- acc_fr: a 42.00, b 39.00, +3.0 [-3.0, +9.0] p 0.5115
- acc_hi: a 39.00, b 34.00, +5.0 [-2.0, +12.0] p 0.2753
- acc_id: a 43.00, b 40.00, +3.0 [-4.0, +10.0] p 0.5914
- acc_it: a 42.00, b 40.00, +2.0 [-6.0, +10.0] p 0.8008
- acc_ja: a 43.00, b 39.00, +4.0 [-3.0, +11.0] p 0.4274
- acc_ko: a 38.00, b 40.00, -2.0 [-11.0, +7.0] p 0.8260
- acc_pt: a 40.00, b 41.00, -1.0 [-8.0, +6.0] p 1.0000
- acc_ru: a 36.00, b 37.00, -1.0 [-9.0, +7.0] p 1.0000
- acc_tr: a 35.00, b 37.00, -2.0 [-8.0, +4.0] p 0.7563
- acc_vi: a 44.00, b 46.00, -2.0 [-9.0, +5.0] p 0.7774
- acc_zh: a 39.00, b 46.00, -7.0 [-14.0, +0.0] p 0.0966
- acc_group_Humanities: a 28.99, b 29.83, -0.8 [-6.0, +4.0] p 0.8100
- acc_group_STEM: a 35.71, b 38.96, -3.2 [-12.3, +5.3] p 0.5350
- acc_group_Social Sciences: a 63.31, b 61.36, +1.9 [-5.0, +10.3] p 0.6883
- acc_group_Medical: a 41.56, b 37.66, +3.9 [-10.7, +17.9] p 0.7201
- acc_group_Other: a 27.38, b 30.95, -3.6 [-7.1, +0.0] p 0.2500
- acc_group_Business: a 45.71, b 35.71, +10.0 [-10.7, +33.3] p 0.4970
- acc_CS: a 40.00, b 50.00, -10.0 [-32.1, +7.1] p 0.5039
- acc_CA: a 55.49, b 56.59, -1.1 [-16.8, +15.1] p 0.9560

### mix21_22b0.75_23b0.5_vs_baseline: possible damage, more than 2 points ruled out: False
- mcnemar: a better 30, b better 47, p 0.0675, pairs 1400
- language leads: ["acc_ko", "acc_ru"]
- acc: a 38.79, b 40.00, -1.2 [-2.8, +0.3] p 0.1480
- acc_ar: a 37.00, b 39.00, -2.0 [-6.0, +2.0] p 0.6223
- acc_de: a 33.00, b 34.00, -1.0 [-6.0, +3.0] p 1.0000
- acc_es: a 47.00, b 48.00, -1.0 [-5.0, +2.0] p 1.0000
- acc_fr: a 39.00, b 39.00, +0.0 [-3.0, +3.0] p 1.0000
- acc_hi: a 36.00, b 34.00, +2.0 [-3.0, +7.0] p 0.6899
- acc_id: a 38.00, b 40.00, -2.0 [-6.0, +2.0] p 0.6224
- acc_it: a 41.00, b 40.00, +1.0 [+0.0, +3.0] p 1.0000
- acc_ja: a 40.00, b 39.00, +1.0 [-4.0, +6.0] p 1.0000
- acc_ko: a 34.00, b 40.00, -6.0 [-12.0, -1.0] p 0.0703
- acc_pt: a 41.00, b 41.00, +0.0 [-7.0, +7.0] p 1.0000
- acc_ru: a 33.00, b 37.00, -4.0 [-8.0, -1.0] p 0.1260
- acc_tr: a 33.00, b 37.00, -4.0 [-10.0, +1.0] p 0.2925
- acc_vi: a 48.00, b 46.00, +2.0 [-2.0, +6.0] p 0.6210
- acc_zh: a 43.00, b 46.00, -3.0 [-8.0, +2.0] p 0.4556
- acc_group_Humanities: a 31.09, b 29.83, +1.3 [-0.7, +3.2] p 0.2938
- acc_group_STEM: a 38.64, b 38.96, -0.3 [-3.0, +2.4] p 1.0000
- acc_group_Social Sciences: a 56.17, b 61.36, -5.2 [-8.8, -1.8] p 0.0134
- acc_group_Medical: a 36.36, b 37.66, -1.3 [-6.4, +3.2] p 0.7488
- acc_group_Other: a 32.14, b 30.95, +1.2 [-7.1, +7.1] p 1.0000
- acc_group_Business: a 28.57, b 35.71, -7.1 [-17.9, +7.1] p 0.4913
- acc_CS: a 48.57, b 50.00, -1.4 [-4.8, +0.0] p 1.0000
- acc_CA: a 54.95, b 56.59, -1.6 [-4.8, +0.9] p 0.5076

### combo_a14_b14_vs_baseline: no damage shown, more than 2 points ruled out: True
- mcnemar: a better 13, b better 14, p 1.0000, pairs 1400
- language leads: []
- acc: a 39.93, b 40.00, -0.1 [-0.8, +0.6] p 1.0000
- acc_ar: a 38.00, b 39.00, -1.0 [-3.0, +0.0] p 1.0000
- acc_de: a 31.00, b 34.00, -3.0 [-8.0, +1.0] p 0.3787
- acc_es: a 49.00, b 48.00, +1.0 [+0.0, +3.0] p 1.0000
- acc_fr: a 39.00, b 39.00, +0.0 [-3.0, +3.0] p 1.0000
- acc_hi: a 34.00, b 34.00, +0.0 [-3.0, +3.0] p 1.0000
- acc_id: a 40.00, b 40.00, +0.0 [-3.0, +3.0] p 1.0000
- acc_it: a 41.00, b 40.00, +1.0 [-2.0, +4.0] p 1.0000
- acc_ja: a 39.00, b 39.00, +0.0 [+0.0, +0.0] p 1.0000
- acc_ko: a 39.00, b 40.00, -1.0 [-3.0, +0.0] p 1.0000
- acc_pt: a 44.00, b 41.00, +3.0 [+0.0, +7.0] p 0.2487
- acc_ru: a 36.00, b 37.00, -1.0 [-3.0, +0.0] p 1.0000
- acc_tr: a 38.00, b 37.00, +1.0 [-2.0, +5.0] p 1.0000
- acc_vi: a 46.00, b 46.00, +0.0 [-3.0, +3.0] p 1.0000
- acc_zh: a 45.00, b 46.00, -1.0 [-3.0, +0.0] p 1.0000
- acc_group_Humanities: a 29.41, b 29.83, -0.4 [-1.4, +0.6] p 0.6736
- acc_group_STEM: a 38.64, b 38.96, -0.3 [-1.5, +0.8] p 1.0000
- acc_group_Social Sciences: a 61.69, b 61.36, +0.3 [-1.5, +2.4] p 1.0000
- acc_group_Medical: a 37.01, b 37.66, -0.6 [-2.1, +0.0] p 1.0000
- acc_group_Other: a 32.14, b 30.95, +1.2 [+0.0, +3.6] p 1.0000
- acc_group_Business: a 37.14, b 35.71, +1.4 [-7.1, +7.1] p 1.0000
- acc_CS: a 48.57, b 50.00, -1.4 [-4.8, +0.0] p 1.0000
- acc_CA: a 56.04, b 56.59, -0.5 [-1.8, +0.0] p 1.0000

## 08 mgsm (`runs/2026-11-22-partc-run/scores/08/mgsm/stats.json`, rows 350, clusters 50)

- observed baseline: acc 20.86, acc_en 24.00, acc_non_en 20.33, cap_pct 9.43, no_prefix_pct 10.29, acc_de 26.00, acc_es 20.00, acc_fr 0.00, acc_ja 20.00, acc_ru 14.00, acc_zh 42.00
- observed c02_nb_L15u1047_k2: acc 19.43, acc_en 34.00, acc_non_en 17.00, cap_pct 11.71, no_prefix_pct 12.86, acc_de 24.00, acc_es 14.00, acc_fr 2.00, acc_ja 16.00, acc_ru 8.00, acc_zh 38.00
- observed h5_a2_n5: acc 15.14, acc_en 22.00, acc_non_en 14.00, cap_pct 5.71, no_prefix_pct 8.29, acc_de 14.00, acc_es 6.00, acc_fr 8.00, acc_ja 10.00, acc_ru 18.00, acc_zh 28.00
- observed mix21_22b0.75_23b0.5: acc 20.86, acc_en 24.00, acc_non_en 20.33, cap_pct 11.71, no_prefix_pct 11.14, acc_de 22.00, acc_es 22.00, acc_fr 6.00, acc_ja 14.00, acc_ru 18.00, acc_zh 40.00
- observed combo_a14_b14: acc 21.71, acc_en 32.00, acc_non_en 20.00, cap_pct 11.14, no_prefix_pct 10.57, acc_de 18.00, acc_es 24.00, acc_fr 8.00, acc_ja 16.00, acc_ru 8.00, acc_zh 46.00

### c02_nb_L15u1047_k2_vs_baseline: possible damage, more than 2 points ruled out: False
- mcnemar: a better 25, b better 30, p 0.5901, pairs 350
- language leads: []
- acc: a 19.43, b 20.86, -1.4 [-5.1, +2.3] p 0.5583
- acc_en: a 34.00, b 24.00, +10.0 [-2.0, +22.0] p 0.2300
- acc_non_en: a 17.00, b 20.33, -3.3 [-7.3, +1.0] p 0.1664
- cap_pct: a 11.71, b 9.43, +2.3 [-0.6, +5.1] p 0.2027
- no_prefix_pct: a 12.86, b 10.29, +2.6 [-0.3, +5.4] p 0.1357
- acc_de: a 24.00, b 26.00, -2.0 [-12.0, +8.0] p 1.0000
- acc_es: a 14.00, b 20.00, -6.0 [-16.0, +4.0] p 0.4611
- acc_fr: a 2.00, b 0.00, +2.0 [+0.0, +6.0] p 1.0000
- acc_ja: a 16.00, b 20.00, -4.0 [-16.0, +8.0] p 0.7530
- acc_ru: a 8.00, b 14.00, -6.0 [-14.0, +2.0] p 0.3789
- acc_zh: a 38.00, b 42.00, -4.0 [-18.0, +10.0] p 0.7904

### h5_a2_n5_vs_baseline: damage, more than 2 points ruled out: False
- mcnemar: a better 19, b better 39, p 0.0119, pairs 350
- language leads: ["acc_de", "acc_es", "acc_zh"]
- acc: a 15.14, b 20.86, -5.7 [-9.7, -2.0] p 0.0112
- acc_en: a 22.00, b 24.00, -2.0 [-16.0, +10.0] p 1.0000
- acc_non_en: a 14.00, b 20.33, -6.3 [-10.3, -2.3] p 0.0049
- cap_pct: a 5.71, b 9.43, -3.7 [-7.4, -0.3] p 0.0789
- no_prefix_pct: a 8.29, b 10.29, -2.0 [-6.3, +2.0] p 0.4210
- acc_de: a 14.00, b 26.00, -12.0 [-24.0, -2.0] p 0.0675
- acc_es: a 6.00, b 20.00, -14.0 [-24.0, -6.0] p 0.0183
- acc_fr: a 8.00, b 0.00, +8.0 [+2.0, +16.0] p 0.1291
- acc_ja: a 10.00, b 20.00, -10.0 [-22.0, +2.0] p 0.2261
- acc_ru: a 18.00, b 14.00, +4.0 [-6.0, +16.0] p 0.7255
- acc_zh: a 28.00, b 42.00, -14.0 [-26.0, -4.0] p 0.0342

### mix21_22b0.75_23b0.5_vs_baseline: no damage shown, more than 2 points ruled out: False
- mcnemar: a better 29, b better 29, p 1.0000, pairs 350
- language leads: []
- acc: a 20.86, b 20.86, +0.0 [-3.7, +3.7] p 1.0000
- acc_en: a 24.00, b 24.00, +0.0 [-8.0, +8.0] p 1.0000
- acc_non_en: a 20.33, b 20.33, +0.0 [-4.3, +4.3] p 1.0000
- cap_pct: a 11.71, b 9.43, +2.3 [-1.7, +6.6] p 0.3445
- no_prefix_pct: a 11.14, b 10.29, +0.9 [-3.1, +4.9] p 0.7856
- acc_de: a 22.00, b 26.00, -4.0 [-18.0, +10.0] p 0.7755
- acc_es: a 22.00, b 20.00, +2.0 [-10.0, +14.0] p 1.0000
- acc_fr: a 6.00, b 0.00, +6.0 [+0.0, +14.0] p 0.2576
- acc_ja: a 14.00, b 20.00, -6.0 [-20.0, +6.0] p 0.5449
- acc_ru: a 18.00, b 14.00, +4.0 [-6.0, +14.0] p 0.7285
- acc_zh: a 40.00, b 42.00, -2.0 [-16.0, +10.0] p 1.0000

### combo_a14_b14_vs_baseline: no damage shown, more than 2 points ruled out: False
- mcnemar: a better 32, b better 29, p 0.7982, pairs 350
- language leads: []
- acc: a 21.71, b 20.86, +0.9 [-2.6, +4.3] p 0.7569
- acc_en: a 32.00, b 24.00, +8.0 [-4.0, +20.0] p 0.3481
- acc_non_en: a 20.00, b 20.33, -0.3 [-4.0, +3.3] p 1.0000
- cap_pct: a 11.14, b 9.43, +1.7 [-1.7, +5.1] p 0.4264
- no_prefix_pct: a 10.57, b 10.29, +0.3 [-2.9, +3.4] p 1.0000
- acc_de: a 18.00, b 26.00, -8.0 [-20.0, +2.0] p 0.2873
- acc_es: a 24.00, b 20.00, +4.0 [-6.0, +16.0] p 0.7331
- acc_fr: a 8.00, b 0.00, +8.0 [+2.0, +16.0] p 0.1325
- acc_ja: a 16.00, b 20.00, -4.0 [-18.0, +10.0] p 0.7888
- acc_ru: a 8.00, b 14.00, -6.0 [-14.0, +2.0] p 0.3727
- acc_zh: a 46.00, b 42.00, +4.0 [-10.0, +18.0] p 0.7713

## 08 ifeval (`runs/2026-11-22-partc-run/scores/08/ifeval/stats.json`, rows 541, clusters 541)

- observed baseline: prompt_strict 51.72, prompt_loose 55.56, inst_strict 60.78, inst_loose 64.25, cap_pct 45.47
- observed c02_nb_L15u1047_k2: prompt_strict 46.67, prompt_loose 49.90, inst_strict 55.86, inst_loose 59.04, cap_pct 47.13
- observed h5_a2_n5: prompt_strict 46.67, prompt_loose 49.90, inst_strict 55.43, inst_loose 58.32, cap_pct 46.03
- observed mix21_22b0.75_23b0.5: prompt_strict 50.10, prompt_loose 52.53, inst_strict 59.04, inst_loose 61.51, cap_pct 48.61
- observed combo_a14_b14: prompt_strict 49.90, prompt_loose 53.94, inst_strict 59.48, inst_loose 63.39, cap_pct 47.50

### c02_nb_L15u1047_k2_vs_baseline: damage, more than 2 points ruled out: False
- mcnemar: a better 47, b better 72, p 0.0274, pairs 495
- language leads: []
- prompt_strict: a 46.67, b 51.72, -5.1 [-9.3, -0.8] p 0.0283
- prompt_loose: a 49.90, b 55.56, -5.7 [-10.0, -1.2] p 0.0140
- inst_strict: a 55.86, b 60.78, -4.9 [-8.5, -1.3] p 0.0079
- inst_loose: a 59.04, b 64.25, -5.2 [-8.8, -1.6] p 0.0056
- cap_pct: a 47.13, b 45.47, +1.7 [-1.7, +5.0] p 0.3903

### h5_a2_n5_vs_baseline: damage, more than 2 points ruled out: False
- mcnemar: a better 43, b better 68, p 0.0223, pairs 495
- language leads: []
- prompt_strict: a 46.67, b 51.72, -5.1 [-9.2, -0.8] p 0.0230
- prompt_loose: a 49.90, b 55.56, -5.7 [-9.9, -1.4] p 0.0102
- inst_strict: a 55.43, b 60.78, -5.4 [-8.8, -1.9] p 0.0035
- inst_loose: a 58.32, b 64.25, -5.9 [-9.4, -2.4] p 0.0009
- cap_pct: a 46.03, b 45.47, +0.6 [-2.8, +3.9] p 0.8276

### mix21_22b0.75_23b0.5_vs_baseline: possible damage, more than 2 points ruled out: False
- mcnemar: a better 36, b better 44, p 0.4340, pairs 495
- language leads: []
- prompt_strict: a 50.10, b 51.72, -1.6 [-5.3, +2.0] p 0.4343
- prompt_loose: a 52.53, b 55.56, -3.0 [-6.6, +0.4] p 0.1151
- inst_strict: a 59.04, b 60.78, -1.7 [-4.7, +1.2] p 0.2774
- inst_loose: a 61.51, b 64.25, -2.7 [-5.7, +0.3] p 0.0874
- cap_pct: a 48.61, b 45.47, +3.1 [+0.0, +6.3] p 0.0732

### combo_a14_b14_vs_baseline: possible damage, more than 2 points ruled out: False
- mcnemar: a better 33, b better 42, p 0.3557, pairs 495
- language leads: []
- prompt_strict: a 49.90, b 51.72, -1.8 [-5.3, +1.6] p 0.3489
- prompt_loose: a 53.94, b 55.56, -1.6 [-5.2, +2.0] p 0.4396
- inst_strict: a 59.48, b 60.78, -1.3 [-4.3, +1.7] p 0.4465
- inst_loose: a 63.39, b 64.25, -0.9 [-4.0, +2.3] p 0.6538
- cap_pct: a 47.50, b 45.47, +2.0 [-1.1, +5.2] p 0.2443

## 2b m-arenahard (`runs/2026-11-22-partc-run/scores/2b/m-arenahard/stats.json`, rows 700, clusters 50)

| method | lpr drop | lpr fail | lpr pass | full % drop | wpr | late switch % | loop % | cap % | unscored (count of scored=0 in perrow) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 90.3 | 90.3 | 90.3 | 0.71 | 83.6 | 8.6 | 0.14 | 100.0 | 0 of 700 |
| c06 | 90.9 | 90.7 | 90.9 | 0.43 | 82.8 | 8.3 | 0.00 | 100.0 | 1 of 700 |
| recover | 90.4 | 90.4 | 90.4 | 0.00 | 80.8 | 9.4 | 0.14 | 100.0 | 0 of 700 |
| instr_end | 91.9 | 91.7 | 91.9 | 0.29 | 85.1 | 7.7 | 0.29 | 99.9 | 1 of 700 |

| a vs b | lpr drop | lpr fail | lpr pass | full % drop | loop % drop | mcnemar a better / b better, p |
|---|---|---|---|---|---|---|
| recover_vs_baseline | +0.1 [-1.6, +1.9] p 1.0000 | +0.1 [-1.6, +1.9] p 1.0000 | +0.1 [-1.6, +1.9] p 1.0000 | -0.7 [-1.6, +0.0] p 0.2493 | +0.0 [+0.0, +0.0] p 1.0000 | 37 / 36, 1.0000 |
| instr_end_vs_baseline | +1.6 [-0.6, +3.7] p 0.1918 | +1.4 [-0.6, +3.6] p 0.2346 | +1.6 [-0.6, +3.7] p 0.2024 | -0.4 [-1.1, +0.0] p 0.4892 | +0.1 [+0.0, +0.4] p 1.0000 | 41 / 31, 0.2888 |
| c06_vs_baseline | +0.6 [-1.4, +2.7] p 0.6550 | +0.4 [-1.6, +2.6] p 0.7932 | +0.6 [-1.4, +2.7] p 0.7041 | -0.3 [-0.9, +0.3] p 0.6218 | -0.1 [-0.4, +0.0] p 1.0000 | 36 / 33, 0.8099 |
| c06_vs_recover | +0.4 [-1.6, +2.6] p 0.7016 | +0.3 [-1.7, +2.4] p 0.8922 | +0.4 [-1.6, +2.6] p 0.7877 | +0.4 [+0.0, +1.0] p 0.1166 | -0.1 [-0.4, +0.0] p 1.0000 | 44 / 41, 0.8284 |
| c06_vs_instr_end | -1.0 [-2.9, +1.0] p 0.3963 | -1.0 [-2.9, +1.0] p 0.4072 | -1.0 [-2.9, +1.0] p 0.4072 | +0.1 [-0.3, +0.6] p 1.0000 | -0.3 [-0.7, +0.0] p 0.5026 | 33 / 40, 0.4828 |

per-language cells with a CI that excludes 0 (drop rule): recover_vs_baseline es +8.0 [+2.0, +16.0]; recover_vs_baseline ru +8.0 [+2.0, +16.0]; instr_end_vs_baseline es +10.0 [+2.0, +18.0]; c06_vs_baseline fr -8.0 [-16.0, -2.0]; c06_vs_baseline ru +8.0 [+2.0, +16.0]

guard vs baseline (baseline loop % 0.14, mean NLL 0.549):

| method | loop % (change) | mean NLL (change) | empty % | guard | source |
|---|---|---|---|---|---|
| c06 | 0.00 (-0.14) | 0.598 (+0.049) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/2b/m-arenahard/c06.guard.json` |
| recover | 0.14 (+0.00) | 0.562 (+0.013) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/2b/m-arenahard/recover.guard.json` |
| instr_end | 0.29 (+0.14) | 0.570 (+0.021) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/2b/m-arenahard/instr_end.guard.json` |

## 2b xl-alpacaeval (`runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/2b/stats.json`, rows 980, clusters 70)

| method | lpr drop | lpr fail | lpr pass | full % drop | wpr | late switch % | loop % | cap % | unscored (count of scored=0 in perrow) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 88.7 | 88.5 | 88.8 | 2.15 | 83.8 | 8.6 | 0.71 | 91.3 | 3 of 980 |
| c06 | 90.5 | 90.2 | 90.5 | 1.43 | 85.2 | 7.8 | 0.61 | 91.9 | 3 of 980 |
| recover | 89.5 | 89.1 | 89.5 | 0.61 | 83.6 | 9.7 | 0.10 | 92.3 | 4 of 980 |
| instr_end | 89.5 | 89.4 | 89.5 | 0.72 | 85.9 | 9.2 | 0.41 | 91.5 | 1 of 980 |

| a vs b | lpr drop | lpr fail | lpr pass | full % drop | loop % drop | mcnemar a better / b better, p |
|---|---|---|---|---|---|---|
| recover_vs_baseline | +0.7 [-1.7, +3.3] p 0.5951 | +0.6 [-1.7, +3.2] p 0.6962 | +0.7 [-1.7, +3.4] p 0.6562 | -1.5 [-3.3, -0.4] p 0.0041 | -0.6 [-1.2, -0.1] p 0.1137 | 48 / 42, 0.5984 |
| instr_end_vs_baseline | +0.7 [-1.0, +2.6] p 0.3927 | +0.9 [-0.9, +2.8] p 0.3966 | +0.7 [-1.0, +2.6] p 0.5164 | -1.4 [-3.7, -0.1] p 0.0373 | -0.3 [-0.7, +0.0] p 0.2553 | 49 / 42, 0.5296 |
| c06_vs_baseline | +1.7 [-0.4, +4.0] p 0.1371 | +1.7 [-0.3, +4.0] p 0.1509 | +1.7 [-0.4, +4.0] p 0.1611 | -0.7 [-2.2, +0.3] p 0.3800 | -0.1 [-0.8, +0.6] p 1.0000 | 57 / 41, 0.1293 |
| c06_vs_recover | +1.0 [-1.4, +3.4] p 0.4273 | +1.1 [-1.3, +3.6] p 0.4269 | +1.0 [-1.4, +3.5] p 0.4678 | +0.8 [+0.2, +1.6] p 0.0261 | +0.5 [+0.1, +1.1] p 0.1291 | 56 / 46, 0.3729 |
| c06_vs_instr_end | +1.0 [-1.4, +3.6] p 0.4840 | +0.8 [-1.6, +3.5] p 0.5981 | +1.0 [-1.4, +3.6] p 0.4982 | +0.7 [-0.0, +1.7] p 0.1574 | +0.2 [-0.4, +0.8] p 0.7618 | 54 / 45, 0.4215 |

per-language cells with a CI that excludes 0 (drop rule): recover_vs_baseline es +5.7 [+1.4, +11.4]; recover_vs_baseline ja +8.6 [+1.4, +17.1]; recover_vs_baseline ko +5.9 [+1.4, +11.7]; instr_end_vs_baseline ja +8.6 [+2.9, +15.7]; c06_vs_baseline hi +7.1 [+1.4, +14.3]; c06_vs_baseline tr +4.3 [+0.1, +9.9]; c06_vs_recover es -5.7 [-11.4, -1.4]; c06_vs_recover hi +11.4 [+4.3, +18.6]; c06_vs_recover tr +5.9 [+1.4, +12.0]; c06_vs_instr_end hi +7.1 [+1.4, +14.3]; c06_vs_instr_end ja -5.9 [-11.8, -1.4]; c06_vs_instr_end tr +7.1 [+1.4, +14.1]

guard vs baseline (baseline loop % 0.71, mean NLL 0.572):

| method | loop % (change) | mean NLL (change) | empty % | guard | source |
|---|---|---|---|---|---|
| c06 | 0.61 (-0.10) | 0.618 (+0.046) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/2b/c06.guard.json` |
| recover | 0.10 (-0.61) | 0.589 (+0.017) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/2b/recover.guard.json` |
| instr_end | 0.41 (-0.31) | 0.602 (+0.030) | 0.0 | pass | `runs/2026-11-22-partc-run/scores/nc-sa/xl-alpacaeval/2b/instr_end.guard.json` |

## 2b lcb-greedy (`runs/2026-11-22-partc-run/scores/2b/lcb-greedy/stats.json`, rows 714, clusters 17)

| method | lpr drop | lpr fail | lpr pass | full % drop | wpr | late switch % | loop % | cap % | unscored (count of scored=0 in perrow) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 69.2 | 63.9 | 71.6 | 25.95 | 88.8 | 2.6 | 2.38 | 83.9 | 55 of 714 |
| c06 | 83.0 | 78.9 | 83.9 | 12.09 | 80.5 | 3.4 | 2.10 | 89.2 | 36 of 714 |
| recover | 89.4 | 84.0 | 89.9 | 5.80 | 82.3 | 2.5 | 1.40 | 86.0 | 42 of 714 |
| instr_end | 78.5 | 74.8 | 79.6 | 15.44 | 85.6 | 2.9 | 1.82 | 87.5 | 34 of 714 |

| a vs b | lpr drop | lpr fail | lpr pass | full % drop | loop % drop | mcnemar a better / b better, p |
|---|---|---|---|---|---|---|
| recover_vs_baseline | +20.3 [+10.5, +31.4] p 0.0008 | +20.2 [+11.5, +30.4] p 0.0005 | +18.3 [+9.1, +29.0] p 0.0010 | -20.1 [-31.4, -10.5] p 0.0006 | -1.0 [-2.1, -0.1] p 0.1253 | 142 / 10, 0.0000 |
| instr_end_vs_baseline | +9.3 [+4.3, +15.1] p 0.0021 | +10.9 [+5.6, +16.9] p 0.0002 | +8.0 [+2.9, +13.3] p 0.0106 | -10.5 [-16.4, -5.6] p 0.0002 | -0.6 [-1.3, +0.0] p 0.2444 | 70 / 7, 0.0000 |
| c06_vs_baseline | +13.8 [+3.6, +25.6] p 0.0222 | +15.0 [+6.0, +25.9] p 0.0033 | +12.3 [+2.1, +23.9] p 0.0458 | -13.9 [-25.0, -4.0] p 0.0204 | -0.3 [-1.4, +0.6] p 0.8437 | 116 / 13, 0.0000 |
| c06_vs_recover | -6.4 [-12.5, -1.2] p 0.0328 | -5.2 [-10.1, -1.1] p 0.0279 | -6.0 [-11.9, -0.8] p 0.0627 | +6.3 [+1.6, +12.1] p 0.0147 | +0.7 [-0.4, +1.8] p 0.3660 | 21 / 55, 0.0001 |
| c06_vs_instr_end | +4.5 [-5.7, +16.0] p 0.4795 | +4.1 [-6.2, +15.4] p 0.5206 | +4.3 [-5.3, +15.4] p 0.4858 | -3.3 [-13.2, +6.2] p 0.5311 | +0.3 [-1.0, +1.5] p 0.7475 | 78 / 44, 0.0027 |

per-language cells with a CI that excludes 0 (drop rule): recover_vs_baseline ar +17.8 [+4.5, +34.6]; recover_vs_baseline de +23.9 [+8.9, +41.3]; recover_vs_baseline es +21.3 [+2.6, +42.2]; recover_vs_baseline fr +27.0 [+10.4, +45.8]; recover_vs_baseline it +19.1 [+4.5, +36.2]; recover_vs_baseline ja +28.0 [+7.8, +49.0]; recover_vs_baseline ko +40.1 [+18.1, +62.5]; recover_vs_baseline pt +19.7 [+2.4, +39.7]; recover_vs_baseline ru +25.7 [+8.9, +44.4]; recover_vs_baseline vi +12.9 [+0.2, +28.6]; instr_end_vs_baseline fr +13.5 [+4.2, +24.6]; instr_end_vs_baseline hi +10.8 [+2.1, +21.3]; instr_end_vs_baseline ja +14.0 [+5.9, +24.5]; instr_end_vs_baseline ko +21.6 [+8.8, +35.4]; instr_end_vs_baseline ru +16.7 [+4.7, +30.6]; instr_end_vs_baseline vi +7.6 [+1.3, +15.0]; instr_end_vs_baseline zh +12.4 [+3.9, +22.4]; c06_vs_baseline ar +17.8 [+2.3, +37.0]; c06_vs_baseline de +15.9 [+4.7, +29.3]; c06_vs_baseline fr +17.2 [+3.0, +33.3]; c06_vs_baseline ja +22.0 [+2.0, +43.1]; c06_vs_baseline ko +28.4 [+9.9, +47.9]; c06_vs_baseline ru +19.4 [+0.8, +38.7]; c06_vs_recover hi -7.4 [-15.3, -1.3]; c06_vs_recover it -13.6 [-25.2, -3.9]; c06_vs_recover ko -11.6 [-24.8, -0.6]

## 2b lcb-long (`runs/2026-11-22-partc-run/scores/2b/lcb-long/stats.json`, rows 238, clusters 17)

| method | lpr drop | lpr fail | lpr pass | full % drop | wpr | late switch % | loop % | cap % | unscored (count of scored=0 in perrow) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 70.5 | 65.1 | 72.7 | 19.09 | 86.4 | 7.3 | 7.56 | 31.9 | 18 of 238 |
| c06 | 78.2 | 73.9 | 79.4 | 10.67 | 78.6 | 8.0 | 11.76 | 39.9 | 13 of 238 |
| recover | 86.1 | 79.8 | 87.4 | 5.45 | 74.4 | 5.9 | 8.40 | 31.9 | 18 of 238 |
| instr_end | 69.9 | 65.5 | 71.8 | 15.70 | 87.4 | 11.7 | 6.30 | 31.1 | 15 of 238 |

| a vs b | lpr drop | lpr fail | lpr pass | full % drop | loop % drop | mcnemar a better / b better, p |
|---|---|---|---|---|---|---|
| recover_vs_baseline | +15.6 [+5.8, +27.2] p 0.0049 | +14.7 [+5.5, +25.6] p 0.0059 | +14.7 [+5.5, +25.6] p 0.0053 | -13.6 [-22.8, -5.9] p 0.0017 | +0.8 [-3.4, +5.9] p 0.8773 | 38 / 3, 0.0000 |
| instr_end_vs_baseline | -0.6 [-7.5, +6.4] p 0.8786 | +0.4 [-5.9, +6.7] p 1.0000 | -0.8 [-7.6, +5.9] p 0.9103 | -3.4 [-6.9, -0.1] p 0.0762 | -1.3 [-2.9, +0.4] p 0.3735 | 13 / 10, 0.6776 |
| c06_vs_baseline | +7.7 [-2.6, +18.9] p 0.2199 | +8.8 [+0.8, +18.9] p 0.0993 | +6.7 [-3.8, +18.1] p 0.2804 | -8.4 [-17.9, +0.2] p 0.1219 | +4.2 [-0.4, +10.1] p 0.2124 | 28 / 5, 0.0001 |
| c06_vs_recover | -7.9 [-13.8, -3.2] p 0.0069 | -5.9 [-9.2, -2.5] p 0.0081 | -8.0 [-13.9, -3.4] p 0.0069 | +5.2 [+1.3, +10.4] p 0.0599 | +3.4 [-2.9, +10.5] p 0.4449 | 7 / 20, 0.0192 |
| c06_vs_instr_end | +8.3 [-0.1, +18.0] p 0.1243 | +8.4 [+0.4, +17.6] p 0.1103 | +7.6 [-0.4, +16.8] p 0.1589 | -5.0 [-14.3, +2.4] p 0.3218 | +5.5 [+0.4, +12.2] p 0.1058 | 27 / 8, 0.0019 |

per-language cells with a CI that excludes 0 (drop rule): recover_vs_baseline fr +31.2 [+11.8, +56.2]; recover_vs_baseline ru +25.0 [+5.9, +47.1]; c06_vs_baseline ko +25.7 [+4.8, +50.0]; c06_vs_recover fr -23.5 [-47.1, -5.9]; c06_vs_instr_end hi +30.0 [+9.7, +53.3]; c06_vs_instr_end vi +20.8 [+1.3, +42.9]

long400 answers that start with the 100-token row (`starts_with_old`): baseline 236 of 238; c06 236 of 238; recover 238 of 238; instr_end 238 of 238

## 2b greedy minus seed 1 sampled (`runs/2026-11-22-partc-run/scores/2b/lcb-greedy/stats_greedy_vs_s1.json`)

| comparison | lpr drop | full % drop |
|---|---|---|
| baseline_greedy_vs_baseline_s1 | -1.1 [-2.7, +0.4] p 0.2553 | +1.3 [-0.7, +3.5] p 0.2845 |
| c06_greedy_vs_c06_s1 | +1.3 [+0.5, +2.3] p 0.0061 | -0.1 [-1.0, +0.8] p 0.8070 |
| recover_greedy_vs_recover_s1 | +0.5 [-1.3, +2.1] p 0.5387 | -0.1 [-1.0, +0.7] p 0.8733 |
| instr_end_greedy_vs_instr_end_s1 | -0.2 [-2.1, +1.9] p 0.8476 | +0.0 [-2.0, +2.1] p 0.9682 |

## 2b global-mmlu (`runs/2026-11-22-partc-run/scores/2b/global-mmlu/stats.json`, rows 1400, clusters 100)

- observed baseline: acc 48.14, acc_ar 52.00, acc_de 47.00, acc_es 49.00, acc_fr 47.00, acc_hi 35.00, acc_id 54.00, acc_it 51.00, acc_ja 44.00, acc_ko 42.00, acc_pt 50.00, acc_ru 52.00, acc_tr 49.00, acc_vi 49.00, acc_zh 53.00, acc_group_Humanities 29.41, acc_group_STEM 53.25, acc_group_Social Sciences 68.51, acc_group_Medical 43.51, acc_group_Other 57.14, acc_group_Business 62.86, acc_CS 41.43, acc_CA 67.58
- observed c06: acc 47.71, acc_ar 50.00, acc_de 46.00, acc_es 47.00, acc_fr 46.00, acc_hi 35.00, acc_id 56.00, acc_it 53.00, acc_ja 41.00, acc_ko 44.00, acc_pt 49.00, acc_ru 52.00, acc_tr 49.00, acc_vi 48.00, acc_zh 52.00, acc_group_Humanities 28.99, acc_group_STEM 52.92, acc_group_Social Sciences 69.16, acc_group_Medical 38.96, acc_group_Other 58.33, acc_group_Business 64.29, acc_CS 35.71, acc_CA 66.48

### c06_vs_baseline: no damage shown, more than 2 points ruled out: True
- mcnemar: a better 20, b better 26, p 0.4614, pairs 1400
- language leads: []
- acc: a 47.71, b 48.14, -0.4 [-1.6, +0.7] p 0.5551
- acc_ar: a 50.00, b 52.00, -2.0 [-6.0, +2.0] p 0.6266
- acc_de: a 46.00, b 47.00, -1.0 [-5.0, +2.0] p 1.0000
- acc_es: a 47.00, b 49.00, -2.0 [-5.0, +0.0] p 0.5014
- acc_fr: a 46.00, b 47.00, -1.0 [-6.0, +3.0] p 1.0000
- acc_hi: a 35.00, b 35.00, +0.0 [-3.0, +3.0] p 1.0000
- acc_id: a 56.00, b 54.00, +2.0 [-2.0, +6.0] p 0.6222
- acc_it: a 53.00, b 51.00, +2.0 [+0.0, +5.0] p 0.5009
- acc_ja: a 41.00, b 44.00, -3.0 [-8.0, +1.0] p 0.3815
- acc_ko: a 44.00, b 42.00, +2.0 [+0.0, +5.0] p 0.4970
- acc_pt: a 49.00, b 50.00, -1.0 [-6.0, +4.0] p 1.0000
- acc_ru: a 52.00, b 52.00, +0.0 [-3.0, +3.0] p 1.0000
- acc_tr: a 49.00, b 49.00, +0.0 [-3.0, +3.0] p 1.0000
- acc_vi: a 48.00, b 49.00, -1.0 [-5.0, +2.0] p 1.0000
- acc_zh: a 52.00, b 53.00, -1.0 [-4.0, +2.0] p 1.0000
- acc_group_Humanities: a 28.99, b 29.41, -0.4 [-1.9, +1.0] p 0.7867
- acc_group_STEM: a 52.92, b 53.25, -0.3 [-2.8, +2.3] p 1.0000
- acc_group_Social Sciences: a 69.16, b 68.51, +0.6 [-2.0, +3.2] p 0.8018
- acc_group_Medical: a 38.96, b 43.51, -4.5 [-10.7, +0.0] p 0.2549
- acc_group_Other: a 58.33, b 57.14, +1.2 [+0.0, +3.6] p 1.0000
- acc_group_Business: a 64.29, b 62.86, +1.4 [-3.6, +7.1] p 1.0000
- acc_CS: a 35.71, b 41.43, -5.7 [-10.7, +0.0] p 0.2440
- acc_CA: a 66.48, b 67.58, -1.1 [-4.5, +2.4] p 0.7450

## 2b mgsm (`runs/2026-11-22-partc-run/scores/2b/mgsm/stats.json`, rows 350, clusters 50)

- observed baseline: acc 35.43, acc_en 56.00, acc_non_en 32.00, cap_pct 20.86, no_prefix_pct 23.43, acc_de 30.00, acc_es 50.00, acc_fr 8.00, acc_ja 26.00, acc_ru 26.00, acc_zh 52.00
- observed c06: acc 39.14, acc_en 54.00, acc_non_en 36.67, cap_pct 28.86, no_prefix_pct 31.14, acc_de 34.00, acc_es 42.00, acc_fr 28.00, acc_ja 22.00, acc_ru 36.00, acc_zh 58.00

### c06_vs_baseline: no damage shown, more than 2 points ruled out: False
- mcnemar: a better 45, b better 32, p 0.1711, pairs 350
- language leads: []
- acc: a 39.14, b 35.43, +3.7 [-2.0, +9.1] p 0.2482
- acc_en: a 54.00, b 56.00, -2.0 [-14.0, +10.0] p 1.0000
- acc_non_en: a 36.67, b 32.00, +4.7 [-1.3, +10.7] p 0.1577
- cap_pct: a 28.86, b 20.86, +8.0 [+2.9, +13.4] p 0.0053
- no_prefix_pct: a 31.14, b 23.43, +7.7 [+2.3, +13.4] p 0.0126
- acc_de: a 34.00, b 30.00, +4.0 [-6.0, +16.0] p 0.7267
- acc_es: a 42.00, b 50.00, -8.0 [-22.0, +6.0] p 0.3904
- acc_fr: a 28.00, b 8.00, +20.0 [+8.0, +32.0] p 0.0056
- acc_ja: a 22.00, b 26.00, -4.0 [-16.0, +8.0] p 0.7499
- acc_ru: a 36.00, b 26.00, +10.0 [-4.0, +24.0] p 0.2993
- acc_zh: a 58.00, b 52.00, +6.0 [-6.0, +18.0] p 0.5093

## 2b ifeval (`runs/2026-11-22-partc-run/scores/2b/ifeval/stats.json`, rows 541, clusters 541)

- observed baseline: prompt_strict 60.81, prompt_loose 63.43, inst_strict 69.03, inst_loose 71.49, cap_pct 43.44
- observed c06: prompt_strict 59.60, prompt_loose 62.83, inst_strict 68.02, inst_loose 70.91, cap_pct 46.21

### c06_vs_baseline: possible damage, more than 2 points ruled out: False
- mcnemar: a better 29, b better 35, p 0.5323, pairs 495
- language leads: []
- prompt_strict: a 59.60, b 60.81, -1.2 [-4.4, +1.8] p 0.5340
- prompt_loose: a 62.83, b 63.43, -0.6 [-3.9, +2.6] p 0.8006
- inst_strict: a 68.02, b 69.03, -1.0 [-3.6, +1.6] p 0.5093
- inst_loose: a 70.91, b 71.49, -0.6 [-3.3, +2.1] p 0.7452
- cap_pct: a 46.21, b 43.44, +2.8 [-0.2, +5.7] p 0.0836
