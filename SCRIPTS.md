# scripts and their hashes

Every file under `scripts/` with its sha256 in this repo. `scripts/` mirrors the study folder, so the paths match the run records. The same list is in `scripts.json`.

## files changed from the study copy

These files differ from the copies that produced the numbers. The only change is a path: an absolute path to the study folder on the author's machine was replaced. The original sha256 is the one in the run records.

| path | original sha256 | sha256 here | change |
|---|---|---|---|
| scripts/runs/2026-11-13-gate5-chain/chain.sh | `bb31dfe428b33dcc58867843f465df6d2dcb01a89c91fe62db0aad15a1b8cb0f` | `dfeecb9812f3bca9f09fac77b6d4735a6ab56709992c4f70b513263d848b3186` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-13-gate5-chain/chain2.sh | `b66865a5784e938a73b53714df75e31756bcc61b37f225f03ca030ffff5faec8` | `ffd1f2ce3202cab911940015de53b859400084e0c6227b590c6d7fe94021080b` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-13-gate5-chain/chain3.sh | `23f7085be562577958dade72d5030f25f43f49a93ae71b8a2bcc8c9cbd7bd6bc` | `691e80f16c9657f7aa78fe3100eec4371424c3317ddb747985e1100f15d5d950` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-13-gate5-chain/chain_b6.sh | `c53138f6f4560b65391c65bbce73f596428939f6ebd6109bf77d2aa56ae40052` | `2fcc6ee4c43eba0cf8cbdc7548e4331c619e6809c58e166ce1bc70ff26312ad1` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-13-gate5-chain/chain_b6_resume.sh | `234ba4d8c7c36c877be9a421442675f87bd907d5f8c0d4a6cad3852e12b41f4d` | `38e9c538b338d5d17500bb85bebff5ff8af68f8ce37efe4ac31776e50e3696e3` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-13-gate5-chain/chain_b6_resume2.sh | `9283a7eedc26ff35287d9717761ccbc5d25342a42936621870d5eaa6c0694470` | `ac86e1b0e6a9ff57d6f9df93a9c5af66508d2bb5ad3ebf9c4fe9b75a2940e527` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-13-gate5-chain/guard_final_dev.sh | `8ce4cb2ef192ad401de1aee6ae657f870d95be9c1095d58f324af794bf3f201a` | `85d43ff1718ea1546a985248cd7dab105e944bd76d76308e36c491a24649e5d4` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-13-gate5-chain/retry_b4.sh | `6feb2ceb19f106f0031a5fa4a5e22995fb59948e8a654eacbacf9b0b51b67dc3` | `c06fe49ba55fcb6dadc3cddfbe3925c7f5d285aad0c299d03df2c30826c4ad4a` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-13-gate5-chain/retry_b6.sh | `28667d90303df29b6ea2636c5672d69f3ce71dbad696c6951d59d2844a1db553` | `2c706a5c1cac5c38058ea9d2cc5687e678e396bc2633798e1867ca6c24f44c6f` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-13-gate5-chain/retry_b4_screen.sh.bak | `e070a5def1d111572cc8127051f8b7d7447d4d59f35a5ab9f1a860fae2b90ab9` | `25fe0096c0cfe23c84859c57ee98450b9772abafc1e8089dc8d497af2db81e34` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-22-partc-08b-side/scripts/pause_at_40.sh | `f34684ea00245ac8bb0cb5ccb2c2de3293dbac9450c2f2e5c5560c7b37d5a778` | `99a31a8f513c22aee607fb4db5ff9f63e9cff276f05a92ee11fe27d849b78ba6` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-22-partc-08b-side/scripts/retry.sh | `fcd874ba23e47d00556f9f7658e3f28adb4b68db2e5f16f53ff6897c78f3cf59` | `af133efe1c5409ef5d046d9d71d6a88535719f3a5b52fd62af898eb3cf3fd1c9` | absolute cd to project root replaced by a path relative to the script |
| scripts/runs/2026-11-22-partc-scripts/DEVIATIONS.md | `7812d634a46be7aed6e68367c05cb08bcbbb848edaa510197c413cdde5be8aa8` | `1cbf62eed8e557e9c8faffee3df9ca2384c75706f746afe360fbd004b4e279a8` | home-relative path to a local clone replaced by a plain description |

## gate 1 baseline (LCB scoring, wrong-language rule)

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-05-gate1-baseline/gen.py | 5548 | `8f84161daa9e6ce0ffa8fddae736d1da0753e02f294bc8ea850665a2dd91f96f` |
| scripts/runs/2026-11-05-gate1-baseline/score.py | 4696 | `ab61c0d92f60ca69ae43c1b7fc688d8e50513aabbae6c2eb4f2a2ed91a31abb8` |
| scripts/runs/2026-11-05-gate1-baseline/wrong_lang.py | 1643 | `f844fe3115ddaca62a5452876e3dce3e5586c6ed1cab8350b5a7dc3d89385671` |
| scripts/runs/2026-11-05-gate1-baseline/security/run-sandboxed.sh | 431 | `a7bbbbec4c63deff60a258f0dbfb71cda27e6dc18137b8c732040e9ab2899dd5` |

## gate 3 methods on test (few-shot, instruction at end, Nie, ReCoVeR)

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-06-gate3-scripts/scripts/generate.py | 7539 | `40c321723250aa4800db690a8541b33538ee166b0defe7033c96e1cccc8f27ba` |
| scripts/runs/2026-11-06-gate3-scripts/scripts/g3common.py | 3249 | `b84356eef01cb6c35d0e4cc504a7146d5133ffd096cdb7129240e8ef1b7d171b` |
| scripts/runs/2026-11-06-gate3-scripts/scripts/recover.py | 4369 | `3698c936a3839b0a093ae230e13a7493d6a0e2c897599f7d3a06e0f70b796c3f` |
| scripts/runs/2026-11-06-gate3-scripts/scripts/recover_collect.py | 2749 | `a93e9a1eec3113cffc55697ede513697c8cc2703fb844208e24c2cb579d0329f` |
| scripts/runs/2026-11-06-gate3-scripts/scripts/nie.py | 5441 | `953032ededd235a147cf9368b21e6962a355907d1e944675007208439fec445c` |
| scripts/runs/2026-11-06-gate3-scripts/scripts/nie_find_neurons.py | 2377 | `97f8f884a8e6e2d36a81eef53668be2ed0695a9566cd9a1e1129272d82619a4c` |
| scripts/runs/2026-11-06-gate3-run/scripts/gen_recover_dev.py | 823 | `e02d528a529103c90e1aef0c7e9818630122d2e36c6b63713577a7e4f53b02a0` |
| scripts/runs/2026-11-06-gate3-run/scripts/gen_variant.py | 2320 | `1d08fde7749ee7a8d08fdfffab786256e9829fdc9706781488b03ddb9293528a` |
| scripts/runs/2026-11-06-gate3-run/scripts/prompt_variants.py | 9303 | `d4e57d0d7486a6a7dcbac8afb933b78fb01a00953b1be056ba3dfb99d441d2f6` |
| scripts/runs/2026-11-06-gate3-run/scripts/merge_instr_end.py | 724 | `dd8c0d56959e16a10690055e3a755f15779a5629b2ab55d12eb10ce0e61b79cd` |
| scripts/runs/2026-11-06-gate3-run/scripts/score_run.sh | 510 | `0b1aa8a26dd7ccd6a92ce46d78652c8044c2e87c186295cfe770d2d3e8af3905` |
| scripts/runs/2026-11-06-gate3-run/scripts/report.py | 3989 | `67e89b752aec775c38f6308857dbfe7ea0f0df6d772b651da3c2e805f1019581` |
| scripts/runs/2026-11-06-gate3-run/scripts/guard.py | 4062 | `b5518c37de33bc347e8c5cb40d7d70d3080754e049fd57479eda0681b626caea` |
| scripts/runs/2026-11-06-gate3-run/scripts/loop_count.py | 617 | `00dfcadcd55e3bf29107e48b5613f4b707a9812085a46ca73fb23768eb8eb961` |
| scripts/runs/2026-11-06-gate3-run/scripts/eyeball.py | 585 | `e6655479f38267c54769646d7862f4af741b9bdeb982267d40e1e82c767c835a` |
| scripts/runs/2026-11-06-gate3-run/scripts/compare_outputs.py | 1188 | `d2b360a4a99504051c481c59fa36fb93fac5a41b17578308cd15dfa5d2551882` |
| scripts/runs/2026-11-06-gate3-run/scripts/make_ids.py | 1968 | `579d1e4d716964e08ac4383e3c560dbbf4d7f39fbac72a59d7686f62c69e6dc9` |

## p50c row

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-08-mit-p50c/scripts/gen_p50c.py | 2095 | `171fbc58668b4a0c5e5e7abc771e00d2d12c31b71631df739904536ad9b44b4c` |
| scripts/runs/2026-11-08-mit-p50c/scripts/diff_check.py | 5967 | `708325bc99f2ecab13349a441005d40eb3c114099c4832c1ec6a57b23c18ce89` |
| scripts/runs/2026-11-08-mit-p50c/scripts/verify_ckpt.py | 2728 | `e00e89dda5604cb7aaefc299cb702a910ec777d234cb71f495ba8a8d08e1e5ec` |

## MMLU-Redux side check

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-08-side-mmlu-redux/scripts/prepare_items.py | 3351 | `75aa0423f0e01858637e776acb4d8bd4382b32bc063d84628a50afe5bf9be134` |
| scripts/runs/2026-11-08-side-mmlu-redux/scripts/mmlu_gen.py | 7060 | `654c354f46a7daee36f5603272469c77db98170e3d90f2d1276dc83d08ec8253` |
| scripts/runs/2026-11-08-side-mmlu-redux/scripts/score_mmlu.py | 5917 | `e0f749b3772ee074af012d0c1a9ad04abea56b6e9f57f3c31b180ccf78d4b134` |

## diff format and apply step (all edits; the 2B edit uses its own common.py)

| path | bytes | sha256 |
|---|---|---|
| scripts/gate4-workspace/tools/apply_diff.py | 5182 | `4ac896d2e62fec6a437ec9574b4d4f05d2ce05de2159fea887835a286840df09` |
| scripts/gate4-workspace/tools/common.py | 2824 | `0b6474a927b12dcf4e1dbce044b3561fd28feb18bd971a5db54874cd7f85c900` |
| scripts/gate5b-workspace/tools/common.py | 2798 | `8c2764bdab6d78b5d4003145dd7491daea9eebea1beff82e3284f8d1b4852c46` |

## gate 4 eval: main table, random controls, seed 2, mono, guard

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-10-gate4-eval/scripts/gen_diff.py | 2572 | `73aa7ef34b42d23d56745ac7faabee69f0b1317826a4141643f674eb3462823b` |
| scripts/runs/2026-11-10-gate4-eval/scripts/make_random.py | 3307 | `74c5d9485f159fbbcbf0b16e0eef8fd7b45dbb783f5f332f3556bec094c42599` |
| scripts/runs/2026-11-10-gate4-eval/scripts/score.sh | 562 | `2e9ebb75b778ac83b1041bebcb5539f36fe211c473da47e48b1ee80c7465509b` |
| scripts/runs/2026-11-10-gate4-eval/scripts/final_table.py | 1804 | `cd8727ccc2a83244c3542a5ebc843942ae1525a608da26a7ffbe12a81a14a198` |
| scripts/runs/2026-11-10-gate4-eval/scripts/check_rows.py | 634 | `da99c6d0f90715d5e0368449920531a24a07e5f07a1f86648d54c79c482c5d6f` |
| scripts/runs/2026-11-10-gate4-eval/scripts/qlib.sh | 1745 | `cced6af7a467e2a497d07d8e5303da419d34e0edcadf5d09abaf3c53a722b456` |
| scripts/runs/2026-11-10-gate4-eval/scripts/run_watch.sh | 3033 | `3c68210bb6785eea6b22edc0b655047da4deca6f396839a0948ed5c389c1941c` |
| scripts/runs/2026-11-10-gate4-eval/scripts/queue_a.sh | 945 | `96b745a6b70daafb5cadbcff8f700e9076d93d441c631b0ee0759d05f7213dae` |
| scripts/runs/2026-11-10-gate4-eval/scripts/queue_b.sh | 601 | `5fa3b32360fea2210535bed9908badfc36e8f7ceb9f491d0348614fbec205b06` |
| scripts/runs/2026-11-10-gate4-eval/scripts/queue_c.sh | 1110 | `86482797773889b808717368f184908a0163d42dc361190e06ae292ad7bde28e` |
| scripts/runs/2026-11-10-gate4-eval/scripts/queue_d.sh | 1151 | `edf2ca120e734b55c948d7eeadfbd826f83b34e5764ac19851f0ec740f327984` |
| scripts/runs/2026-11-10-gate4-eval/scripts/queue_resume.sh | 1162 | `b4dade62ec7c96d8396465743aae968a13095989763115dc0d9f4388e073c8fd` |
| scripts/runs/2026-11-10-gate4-eval/scripts/queue_resume2.sh | 1053 | `2beeef91fc9fe2e760e0e3c1892fcf79cd75575eb49f00a193023bba165cd73c` |

## statistics (cluster bootstrap, permutation)

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-11-stats-gate4/scripts/per_prompt.py | 7403 | `556f8d2573679636174d26d8d0dde10fce94e705e9b6b10c5b41e511739a38d9` |
| scripts/runs/2026-11-11-stats-gate4/scripts/stats.py | 14227 | `e69d3dd2ffdf64cb1683ad1787ba775ff01f97dcd152988f1a319dbf225afbaa` |
| scripts/runs/2026-11-11-stats-gate4/scripts/make_tables.py | 5127 | `a70692a687a61b24e34b8cd77b67e834b87773d12586148d69ad96fabe33d471` |

## blind LLM judge

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-11-judge/scripts/label_lines.py | 1931 | `15f995b708d3afb8faed84562aad23b874e61ac27e27d990b391b6c36f9392b2` |
| scripts/runs/2026-11-11-judge/scripts/check_labels.py | 2678 | `125759ff38d122c2d3f1bb0e47b7212a052b487eb35972bd222e7e4848e28d28` |
| scripts/runs/2026-11-11-judge/scripts/sample.py | 6729 | `6093d2c2e95350703c66b142edfb292dc6d352a0d2ee66d9d30a8f4d064ea03a` |
| scripts/runs/2026-11-11-judge/scripts/leak_check.py | 6720 | `fddeb4d8af9c9e9da4020249f4b43cff205036d9c49178647bab8359e70cecd9` |
| scripts/runs/2026-11-11-judge/analysis/audit_tools.py | 785 | `aacb5b708074bd534e241fa3f5daaa77a58ee51674e2cd6b1fc3ec0b42dcdc5b` |
| scripts/runs/2026-11-11-judge/analysis/audit_check.py | 3032 | `a072577fb9c8d06076e9c7837c613727ed6de505eb5022179d5f5b9ed61f29e5` |
| scripts/runs/2026-11-11-judge/analysis/unblind.py | 13659 | `7f260862e4011e48a4b258d86bed83b71a3f36a7f569884c507052ee765dc9d2` |
| scripts/runs/2026-11-11-judge/analysis/make_tables.py | 3949 | `b4483e7457da72b5db18f7477d6cf21ad9bdc34c586448ecaddfb6262f2abddf` |

## part A eval (editors 1 to 3) and banned-read audit

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-11-gate5a-eval-prep/scripts/check_frozen.py | 2986 | `9872fb46e9413f00c440465ea3d86711003f6f2cd590c988697cfdf59a33fd18` |
| scripts/runs/2026-11-11-gate5a-eval-prep/scripts/gen_diff.py | 2758 | `8502de989e8b819244b6d107490b8fd4a67bb74e4a4477aadeb809e0d4a8c1c8` |
| scripts/runs/2026-11-11-gate5a-eval-prep/scripts/make_random.py | 9062 | `a8e5625b01177beba9834bb011fb52ba7017c891bbc164e3b0dd8db085f02d17` |
| scripts/runs/2026-11-11-gate5a-eval-prep/scripts/score.sh | 562 | `2e9ebb75b778ac83b1041bebcb5539f36fe211c473da47e48b1ee80c7465509b` |
| scripts/runs/2026-11-11-gate5a-eval-prep/scripts/final_table.py | 1804 | `cd8727ccc2a83244c3542a5ebc843942ae1525a608da26a7ffbe12a81a14a198` |
| scripts/runs/2026-11-11-gate5a-eval-prep/scripts/check_rows.py | 634 | `da99c6d0f90715d5e0368449920531a24a07e5f07a1f86648d54c79c482c5d6f` |
| scripts/runs/2026-11-11-gate5a-eval-prep/scripts/qlib.sh | 3230 | `2c169c4c43399b4642fa1b91159e0ce3df1e8f2e0f3e690b914c587f8cb61835` |
| scripts/runs/2026-11-11-gate5a-eval-prep/scripts/run_watch.sh | 3243 | `3a372a6ffb44c2d89774303b9c1ebed47ec0789982d96c7aa9d98c39eff0cb67` |
| scripts/runs/2026-11-11-gate5a-eval-prep/scripts/queue_eval.sh | 7243 | `1a53cada5d81c9a4409556780a3172a9ef21741672021d84425be440fe8f2956` |
| scripts/runs/2026-11-11-gate5a-eval-prep/scripts/audit.py | 11081 | `1897cb4f9286512cd9f56f192d7453deff920a899c3e55c7e31350d504affba8` |

## part B scripts: 2B queues, shim, controls, tables, stats (B1 to B6)

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-11-gate5b-scripts/scripts/check_rows.py | 634 | `da99c6d0f90715d5e0368449920531a24a07e5f07a1f86648d54c79c482c5d6f` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/env_check_2b.py | 7454 | `e6268a02dadced0788b5398a246d5bedb7dc59922257c1289d2cdb6123ef9d41` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/final_table.py | 1804 | `cd8727ccc2a83244c3542a5ebc843942ae1525a608da26a7ffbe12a81a14a198` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/gen_diff.py | 2946 | `f55ba852e3081d4364a2958bcce59b1c83ac3c372fcad090dee440471c674856` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/make_data.py | 3756 | `95463651c016ce28a60b32dbfaccb0ad2462f75e374dfc4746097def7d87fbf2` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/make_random.py | 9062 | `a8e5625b01177beba9834bb011fb52ba7017c891bbc164e3b0dd8db085f02d17` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/make_tables.py | 5238 | `f343d29f0f0c61e46d7f14a5c8a71141c0f55190c3fa30cd89e2448c61ee587d` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/per_prompt.py | 7732 | `5396438d0912555307993bf84b04f0256a1d36ab432a8363982575f2b549165f` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/run_2b.py | 3374 | `29f06422535bdd58f04fc0232ea1f2b381a15335f5ab01ee2ff6bab5b03ba6b4` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/stats.py | 14577 | `757458c22dca8b9b47b8ef23095a8e06d49c049fa221f846144426b16ae30bfc` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/timing_summary.py | 1630 | `8b69c1e552a740cdacd1f899cc38207a06fc8a7201f7204322e787201e870cbc` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/gate2/step1_summary.py | 5787 | `eca3be9961ca21ea3d977dcd9ed6a1438dd2581e9fa391495ee69688d58394ea` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/gate2/step2_lens.py | 9536 | `537b7063116ce0bf222f842907b0b69fabc67930e72744ace743417cfe53c3d4` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/gate2/step2_token_labels.py | 4014 | `a84e27e147d629a8f5e62ef7dc21729a81b109529adff8162a9f9d1e85707334` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/qlib.sh | 3666 | `b3ad76b835c5dda2c1ea093b98371ed043f63f21c2f68fa8bec214b546fd96e5` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/queue_b1.sh | 4184 | `c0722ccc58976d8f9034f965767743869740abcd683ff987fac6fd957f9da25e` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/queue_b2.sh | 2588 | `f9b9f0a0c45c2372891456070076ef6d2290c84650fa025e280e5686f1d76cdb` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/queue_b3.sh | 2029 | `faf2a2f35edf27397afa7c3de1369c76511be8ad776de68d68fc7eb124c53d76` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/queue_b4.sh | 5267 | `14d17f73493922aea955285ecbfd19db98ebe00aec972bb4bc82549e8526947b` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/queue_b6.sh | 8432 | `bbb78f84312a095b151cc122b49db861d46595776a47cda4b8e451bc382389c7` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/run_watch.sh | 3144 | `29a75b853d6b057a407e49f10cf9f1986c61fd14ffb45c77ce70d860a5f362a3` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/score.sh | 562 | `2e9ebb75b778ac83b1041bebcb5539f36fe211c473da47e48b1ee80c7465509b` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/qlib_v1.sh.bak | 3552 | `756570fb3881ca6e3d10bbc8a8c6ad4193f45ff6629d9b957d1ca0bc22db0e91` |
| scripts/runs/2026-11-11-gate5b-scripts/scripts/queue_b4_v1.sh.bak | 4896 | `dd9325a8c17c537b41c4bd6dcfb6c1d424c303b3063384ebe55e21dbad318f94` |

## part B script tests (cpu, mock tools)

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-11-gate5b-scripts/tests/gen_diff_mocktools.py | 2977 | `b239f2e48b17b927b9ed61651e21ab43e4f5325a6616d84ed91a223a00b7abbb` |
| scripts/runs/2026-11-11-gate5b-scripts/tests/smoke_2b_recover.py | 3943 | `003d7c462560b0c236b0eb11d3b4a9db12dde416479f8013ecd117a98852b298` |
| scripts/runs/2026-11-11-gate5b-scripts/tests/test_make_random.py | 5614 | `c3df5c83f10a8b03531b14805c4c0ac779be38077c1bb0d211c0a7be352e8474` |
| scripts/runs/2026-11-11-gate5b-scripts/tests/test_make_random_large.py | 1648 | `8c4d6abcf9c0473fa12c733f848844377f84209b35586798a9b8e828384d516c` |
| scripts/runs/2026-11-11-gate5b-scripts/tests/mock_tools/apply_diff.py | 5182 | `4ac896d2e62fec6a437ec9574b4d4f05d2ce05de2159fea887835a286840df09` |
| scripts/runs/2026-11-11-gate5b-scripts/tests/mock_tools/common.py | 2822 | `fdb4d6201a9e3b5aaaaee955c633985da4de79c2c5472c29ffe6ad0e5fd65593` |

## gpu chain: part A editor 3 eval and part B queues, resume and retry wrappers

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-13-gate5-chain/chain.sh | 1639 | `dfeecb9812f3bca9f09fac77b6d4735a6ab56709992c4f70b513263d848b3186` |
| scripts/runs/2026-11-13-gate5-chain/chain2.sh | 1243 | `ffd1f2ce3202cab911940015de53b859400084e0c6227b590c6d7fe94021080b` |
| scripts/runs/2026-11-13-gate5-chain/chain3.sh | 1243 | `691e80f16c9657f7aa78fe3100eec4371424c3317ddb747985e1100f15d5d950` |
| scripts/runs/2026-11-13-gate5-chain/chain_b6.sh | 576 | `2fcc6ee4c43eba0cf8cbdc7548e4331c619e6809c58e166ce1bc70ff26312ad1` |
| scripts/runs/2026-11-13-gate5-chain/chain_b6_resume.sh | 578 | `38e9c538b338d5d17500bb85bebff5ff8af68f8ce37efe4ac31776e50e3696e3` |
| scripts/runs/2026-11-13-gate5-chain/chain_b6_resume2.sh | 459 | `ac86e1b0e6a9ff57d6f9df93a9c5af66508d2bb5ad3ebf9c4fe9b75a2940e527` |
| scripts/runs/2026-11-13-gate5-chain/guard_final_dev.sh | 505 | `85d43ff1718ea1546a985248cd7dab105e944bd76d76308e36c491a24649e5d4` |
| scripts/runs/2026-11-13-gate5-chain/retry_b4.sh | 806 | `c06fe49ba55fcb6dadc3cddfbe3925c7f5d285aad0c299d03df2c30826c4ad4a` |
| scripts/runs/2026-11-13-gate5-chain/retry_b6.sh | 806 | `2c706a5c1cac5c38058ea9d2cc5687e678e396bc2633798e1867ca6c24f44c6f` |
| scripts/runs/2026-11-13-gate5-chain/retry_b4_screen.sh.bak | 810 | `25fe0096c0cfe23c84859c57ee98450b9772abafc1e8089dc8d497af2db81e34` |

## part B statistics (2B, cluster bootstrap, permutation)

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-20-stats-2b/scripts/make_tables.py | 5970 | `121922592e97f609092dacd2f517f755c346b617399d12d1c37db05c7f47e1bb` |
| scripts/runs/2026-11-20-stats-2b/scripts/per_prompt.py | 8056 | `c84522e30f234f21ec142f62963e8d720de1f77816b1a6523f8acf5f42162387` |
| scripts/runs/2026-11-20-stats-2b/scripts/stats.py | 16502 | `cf24df6fbf335d1628cc73538de136d4d31878ab762234b64626fe79def96245` |

## paper figures and tables

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-17-paper-figures/scripts/check_svg.py | 1252 | `7dccfa20cfcfce55a4f8c1d6eaf48630de7a5cf0cdd10d7161f1392cb5d6f36a` |
| scripts/runs/2026-11-17-paper-figures/scripts/common.py | 6258 | `55a1bb1f4e6e13bd57899c438ca463579b898ed628ad6dfd7da1c95dbf73cc2f` |
| scripts/runs/2026-11-17-paper-figures/scripts/fig1_main_08b.py | 5969 | `52206c83b5db78f84746a4af83cf6feb07b271c10cd4b6c177997b2759f77390` |
| scripts/runs/2026-11-17-paper-figures/scripts/fig2_forest_vs_recover.py | 4697 | `4e84147f5fead1d40c0f548b6c3d087e0da18f088703f0128d16f271587a5781` |
| scripts/runs/2026-11-17-paper-figures/scripts/fig3_recover_sweep.py | 11659 | `e1d738042088b7b96cb54df681c3037b1306b24ad9cf5965a30e00d42ed78063` |
| scripts/runs/2026-11-17-paper-figures/scripts/fig4_partb_2b.py | 6363 | `1d99d41adfbbed2cab265e2c8bbc9a5d699d5e455c5186f51e1c19fe88c91332` |
| scripts/runs/2026-11-17-paper-figures/scripts/fig5_mechanism_probe.py | 8177 | `e42fe3fc002d3c77f1dd4ecb4a5525a0fb2814e7d2801a53d187b40d298c75e9` |
| scripts/runs/2026-11-17-paper-figures/scripts/fig6_logit_lens.py | 5499 | `7546a09e15e30c31cc9f139a28f68eb99ab065e41b05641196c84637d1f3845d` |
| scripts/runs/2026-11-17-paper-figures/scripts/fig7_per_language.py | 4595 | `5229141327df11250850bf1aa936d2bedceee002ed873d1db8240858c7e36775` |
| scripts/runs/2026-11-17-paper-figures/scripts/hash_files.py | 1585 | `96d3ebf461503196b9df1d5cc2539ee2d1f5d1ff9c79092becf67fb24e823f5d` |
| scripts/runs/2026-11-17-paper-figures/scripts/run_all.sh | 478 | `cfee6a54e100a821a59aab53ef2c9c142a14895c409f54cd8e9895c54ba410fb` |
| scripts/runs/2026-11-17-paper-figures/scripts/tab_costs.py | 4716 | `ed4b06b10335d5cc6284433281677e13e0643b527c8d52df2806e928b23f437e` |
| scripts/runs/2026-11-17-paper-figures/scripts/tab_examples.py | 6961 | `e34ec9b06e93f2a9eec35b938ed553b6a34e5230fbf91ad20d5bbff4d9a79574` |
| scripts/runs/2026-11-17-paper-figures/scripts/tab_guard.py | 7415 | `a04ea4e29551955c0fe511b4c48e9ffa9fbe7cc396d992a182b164c6732961fe` |
| scripts/runs/2026-11-17-paper-figures/scripts/tab_main_08b.py | 5487 | `4a63e63d627ec3e8a890a2b39352860f5ce9bcebcbcd11cd17eeec3c78174b8c` |
| scripts/runs/2026-11-17-paper-figures/scripts/tab_partb_2b.py | 12898 | `207e89258163a864715a71b5e55dc2f764c24b447e83f7859bd5482e1a674bac` |

## splits

| path | bytes | sha256 |
|---|---|---|
| scripts/splits/make_split_v2.py | 6646 | `43334e12da620cda6f9cb1f902ca46314e2efa45caf6afcb821bc8a20a0f6f61` |

## part A by-eye and unscored-answer checks

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-12-gate5a-checks/scripts/unscored.py | 9408 | `57196a3f44d83900a86aff4b7b4a422e72d52dbaae89345122254678ceeb33f1` |
| scripts/runs/2026-11-12-gate5a-checks/scripts/unscored_ed3.py | 9634 | `b55558d2e7adf7468e5ef23b725a53416fa215d00e8e14ab8fb58784132e60ec` |

## part A intervals and summary tables

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-13-gate5a-summary/scripts/make_tables.py | 5010 | `43e3d1ab3d68d0804a5e9b7b914b223ebdba6f19d6c98c5db991d8c9ae12b3cf` |
| scripts/runs/2026-11-13-gate5a-summary/scripts/summary.py | 9101 | `2d20498018c96216a14b223d3ebcdb22a00b502d09a0322d1545e32a08d4a091` |

## part C 0.8B side run (monolingual LCB and MMLU-Redux, editors 1 to 3)

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-22-partc-08b-side/scripts/pause_at_40.sh | 974 | `99a31a8f513c22aee607fb4db5ff9f63e9cff276f05a92ee11fe27d849b78ba6` |
| scripts/runs/2026-11-22-partc-08b-side/scripts/queue_side.sh | 2100 | `8b05878de2ad55d042ab7a37e51c34aab16cd2f2ec44306fd821b20d64aceed7` |
| scripts/runs/2026-11-22-partc-08b-side/scripts/retry.sh | 1096 | `af133efe1c5409ef5d046d9d71d6a88535719f3a5b52fd62af898eb3cf3fd1c9` |
| scripts/runs/2026-11-22-partc-08b-side/scripts/score_side.sh | 1464 | `394dc197fd55cc741b92ff3ffbab258f328a766423d900d4d2ebaee4762d1f95` |
| scripts/runs/2026-11-22-partc-08b-side/scripts/table.py | 1965 | `dcdaab9c2d12e43fd8ff26abdf5bdfc48381d1fbd9b25b8b39a5baa37adc12fe` |

## part C prompt sets (fetch, verify, build)

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-22-partc-protocol/scripts/build_sets.py | 22971 | `84d622465d6c3b951cf2e735324d7bf16298ef68e0b6c2e1cdd945e5f889dbf1` |
| scripts/runs/2026-11-22-partc-protocol/scripts/fetch.py | 1997 | `cc3878e4bc5ace0f0d20365c95d8a38fd927dada243f8502b6029630e6b5f9eb` |
| scripts/runs/2026-11-22-partc-protocol/scripts/verify_raw.py | 1096 | `74c50f3eeb6955bde305279463e5c73c7c3107122b478b79db340fb14f53608f` |

## part C generation, scoring and statistics

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-22-partc-scripts/scripts/check_frozen_c.py | 4846 | `91a55e4c0522993984f410ada126a461999514481803b1a7cd6f810344bd3b79` |
| scripts/runs/2026-11-22-partc-scripts/scripts/check_sets.py | 1755 | `cab38494f492ee3ab98ae84fcd05910b2543ffa1484d7aed743ab4df18b226be` |
| scripts/runs/2026-11-22-partc-scripts/scripts/gmmlu_logit.py | 5085 | `3de9dc961135cad9550c009e550572f89a63266c21706d42e994ec026fdbcf76` |
| scripts/runs/2026-11-22-partc-scripts/scripts/ifeval_checks.py | 9514 | `5a8e9682a803d8c9d3a8b81f83d5475e420da8d58d18a9c3064a447899afab60` |
| scripts/runs/2026-11-22-partc-scripts/scripts/ifeval_score.py | 3259 | `c28c6e6ff18208c756eca02a0f4b49891a98ab8cfcae07a361169baafc87b3aa` |
| scripts/runs/2026-11-22-partc-scripts/scripts/loops_rows.py | 1878 | `d5628b5410a9793bd669cb4546fb92a46a3cdf569e4cb22d1f8ec1fdc47a1d3d` |
| scripts/runs/2026-11-22-partc-scripts/scripts/mgsm_score.py | 3512 | `de576b093012ca76bcd43c8d9849e404a8194fd3cc4c6e88691f1d3fb94ed96c` |
| scripts/runs/2026-11-22-partc-scripts/scripts/partc_gen.py | 7145 | `9a840bbaf13f35039e04a36f27487a4b1037b1052270a3bcab7c63085f1057a2` |
| scripts/runs/2026-11-22-partc-scripts/scripts/per_row_lcb.py | 4503 | `e5b334a644eca8a41a19a7ecfbb81c7ebbfa41b440975b3e46de36a4e053f9d6` |
| scripts/runs/2026-11-22-partc-scripts/scripts/precheck_c.sh | 2922 | `f1c707a9d50e34b4aec50a2cbf97988dcd653e2178cddc4a5281c1fc46662890` |
| scripts/runs/2026-11-22-partc-scripts/scripts/queue_c.sh | 15195 | `2c712a1a80bb6e46bca65f47f48626d7aad122047748ecc4b54b609afc81a4d0` |
| scripts/runs/2026-11-22-partc-scripts/scripts/retry_c.sh | 1801 | `97e33b7e726077d033ef6d67db3de059881241b68c1649cce91a13417df309fb` |
| scripts/runs/2026-11-22-partc-scripts/scripts/same_rows.py | 2532 | `7d14647fd7e3d7bf978425d0b01632b7af8a94b4ee0909be87b505946211540e` |
| scripts/runs/2026-11-22-partc-scripts/scripts/stats_c.py | 13379 | `de2ac253ef97d8fbf266bc577aecf508f041ec51d6ac765d4229cfffb096e33c` |
| scripts/runs/2026-11-22-partc-scripts/DEVIATIONS.md | 4590 | `1cbf62eed8e557e9c8faffee3df9ca2384c75706f746afe360fbd004b4e279a8` |

## part C blind judge on the 2B

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-24-judge-2b/analysis/audit_check.py | 5843 | `b559410bbe673c10d92f02a572c1c2e983cfd9e8c02b8f6b646d7f2febfe8f81` |
| scripts/runs/2026-11-24-judge-2b/analysis/audit_tools.py | 785 | `aacb5b708074bd534e241fa3f5daaa77a58ee51674e2cd6b1fc3ec0b42dcdc5b` |
| scripts/runs/2026-11-24-judge-2b/analysis/extra.py | 2693 | `9b1bd6324e8b2e084e567e47308a6395426eb045d67c9f7a4839f3e8bc75d8b7` |
| scripts/runs/2026-11-24-judge-2b/analysis/make_tables.py | 3949 | `a079db324fe5a86857b40899adfe665a6a6ec8f50a2843aea04fd6cfa54e9856` |
| scripts/runs/2026-11-24-judge-2b/analysis/unblind.py | 13661 | `d08272f9ec6bf463a7297989db3ff2f24ebad7d4f640e79a892e0c9e79cf2545` |
| scripts/runs/2026-11-24-judge-2b/scripts/check_labels.py | 2756 | `0559513dd4ab9390f4496867633358f9d956841008631c118523c41be04c7f5b` |
| scripts/runs/2026-11-24-judge-2b/scripts/label_lines.py | 1931 | `15f995b708d3afb8faed84562aad23b874e61ac27e27d990b391b6c36f9392b2` |
| scripts/runs/2026-11-24-judge-2b/scripts/leak_check.py | 6742 | `70337d35c44c1574208a1f98a64f612f2b23bd206ba7de9bd7001493c4552b89` |
| scripts/runs/2026-11-24-judge-2b/scripts/sample.py | 7867 | `625db4e935fc4c64bbc2defaa1263a49d95c45db963968d68727245380ffcc96` |
| scripts/runs/2026-11-24-judge-2b/scripts/summary.py | 3063 | `78a1bfc78278f0e8efc109359dd2d7f1fea27c366c4be075587d61bc23490b2a` |

## part C figures and number tables

| path | bytes | sha256 |
|---|---|---|
| scripts/runs/2026-11-24-partc-figures/MANIFEST.md | 1298 | `973262cb51f63c00d169e004114bf08565dbff2daade1f05ad279c1dd0c08760` |
| scripts/runs/2026-11-24-partc-figures/figures/figc1_crossling_gain.svg | 27576 | `dd521548f329c05ee39ef2b15d411eaf65ea31f78775c348a900ce8f15ed5db4` |
| scripts/runs/2026-11-24-partc-figures/figures/figc1_crossling_gain.txt | 686 | `9abf7ef6b96672437d949d491c1cf455f857c1701efdb09e106fee16e1cf9bc2` |
| scripts/runs/2026-11-24-partc-figures/figures/figc1_crossling_gain.values.tsv | 18335 | `a15ed8d0660c22f33f073e6f35eaa203fce8f88910ec24405181832a1e57a51e` |
| scripts/runs/2026-11-24-partc-figures/figures/figc2_damage.svg | 14326 | `a9a5b9dd25fbf22dc9ed497d211806d7af15cd2ea8cdcc3a8f04b5c105e68955` |
| scripts/runs/2026-11-24-partc-figures/figures/figc2_damage.txt | 870 | `71aeb11d4acfd6e8394675c61720a3a29bd076fceed8b4b4e71140060109c540` |
| scripts/runs/2026-11-24-partc-figures/figures/figc2_damage.values.tsv | 9053 | `a815dd26d95aa03eb1f061d28b13e8b78f00e83d11b271dda92febe59448ae44` |
| scripts/runs/2026-11-24-partc-figures/figures/figc3_judge_2b.svg | 11845 | `1d157249e54832ced916b4ff0e7b03d80f735a65fe1fa5f6609c0d0f5d142b3f` |
| scripts/runs/2026-11-24-partc-figures/figures/figc3_judge_2b.txt | 655 | `fa4fc761212a813b35e11db09f93583288235a35ac005f26c300760ff01c9a05` |
| scripts/runs/2026-11-24-partc-figures/figures/figc3_judge_2b.values.tsv | 4513 | `dfc904cfc251bfba9349d4686c87003c73144a430ddfcd72debcf25ec12b3722` |
| scripts/runs/2026-11-24-partc-figures/scripts/common.py | 3566 | `136c769e1dbf101ba2377a05e848a2a937158c243fd56786cadfa17e802e1a67` |
| scripts/runs/2026-11-24-partc-figures/scripts/extract.py | 6603 | `f0f7f4ce5d42a0660a83a426ed4248dae5cc6ae9ba45e5e7da906be578a90709` |
| scripts/runs/2026-11-24-partc-figures/scripts/figc1_crossling_gain.py | 3238 | `af14d0e697233ff9ee4463a5950c07b9c64925f0da4d7999e4bf21a67f9c154d` |
| scripts/runs/2026-11-24-partc-figures/scripts/figc2_damage.py | 3515 | `ded98b6e09ba8ac6a824935bccbc0865aa163be7d40240512f39aa2c9de89aed` |
| scripts/runs/2026-11-24-partc-figures/scripts/figc3_judge_2b.py | 3327 | `0cfca679f1978a7fcb863b41c75a02b9cda278488dab9568a2e3815fc333ed3a` |
| scripts/runs/2026-11-24-partc-figures/scripts/run_all.sh | 325 | `09396ffddbbc37d00e52b658ef18b7930b1497ec9a265719321d2ec97649ea35` |
| scripts/runs/2026-11-24-partc-figures/tables/partc_numbers.md | 60451 | `358c7e0fee525c41b985634893b5569aa735f34ef4d3ee80a2d9ea184d7345c6` |
