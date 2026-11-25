# IFEval scorer: differences from the official checker

`scripts/ifeval_checks.py` is a stdlib port of the IFEval instruction checks (google-research `instruction_following_eval`, Apache-2.0). No downloaded or third-party code is imported or run. The port was written from the checker text as kept in a local clone of lm-evaluation-harness (`lm_eval/tasks/ifeval/instructions.py` and `utils.py`, commit `c562a075e7fd83af5cd135d0fe6a860fa0d5fe73`), read as text only. lm-eval's copy is itself a port of the Google code. Its `check_following` bodies were diffed (whitespace, comments and docstrings removed) against a second copy, the VoiceBench vendor copy in a local NeMo Gym checkout (`resources_servers/voicebench/vendor/instruction_following_eval/`): 29 classes in each, 6 differ in style only (`bool(x)` vs `True if x else False`, a loop vs `any`, `list()` vs `[]`), none in behaviour. The Google repository itself was not available offline, so the Google file was not compared directly.

Only the 21 instruction ids that the part C IFEval rows score are ported. `length_constraints:*` is left out on purpose (PROTOCOL.md section 3).

## changes

1. **`language:response_language`**: `langdetect.detect(value) == language` is replaced by the top label of fastText `lid.176.bin` (the file LCB scoring already uses, `runs/2026-11-05-gate1-baseline/scoring_workdir/lid.176.bin`). Newlines are joined into spaces first, because fastText reads one line. No score threshold is used, since `langdetect.detect` also returns its top language. (LCB's `compute_metrics.langid` uses a 0.3 threshold; that rule is not used here.) The two tools give different answers on some texts, especially short or mixed ones.
2. **langdetect errors**: the official code counts the instruction as followed when langdetect raises `LangDetectException`, which happens when the text has no usable features. fastText never raises. The stand-in raises when the text has no letter at all (`str.isalpha` false for every character), and that case is counted as followed, as in the official code.
3. **`change_case:english_capital`**: same fastText stand-in for `langdetect.detect(value) == "en"`, but the text is lower-cased before the language id. On all-caps English, fastText gives low or wrong labels (measured: "THIS IS A LETTER TO MY FRIEND ABOUT THE WEATHER IN LONDON." gives `en` at 0.48; "HELLO" gives `uk`). The upper-case condition itself is still checked on the original text with `value.isupper()`.
4. **`change_case:english_lowercase`**: same fastText stand-in, on the text as given (it is lower case when this check matters).
5. **`change_case:capital_word_frequency`**: `nltk.word_tokenize` is replaced by `word_tokenize()` in the port: split on whitespace, split off leading and trailing punctuation, split the clitics `'s 'm 'd 'll 're 've n't`. Hyphens and inner dots stay inside a word, as in nltk. Known gaps against nltk: no sentence splitting step (only matters for a final dot, which is split off anyway), no special handling of quotes written as two backticks, and none of nltk's rarer contraction rules (`cannot`, `gonna`, `'tis`). Only tokens that are all upper case count, so most of these gaps do not change the count.
6. **kwargs**: as lm-eval `utils.py`, keys with a falsy value are dropped before the check (`{k: v for k, v in kwargs.items() if v}`). The Google `evaluation_main.py` reads kwargs from its own input file; the HF rows used here have no null kwargs for the scored ids (checked by the test over all 541 rows).
7. **default arguments**: the official `build_description` picks random values when an argument is missing. The port never does that: a missing argument is an error. Every scored row has all its arguments (the test runs every scored instruction of all 541 rows).

## not changed

Strict and loose rules (`utils.test_instruction_following_strict` / `_loose`, the 8 loose variants in the same order), empty-response rule (`response.strip()` must be non-empty), every regex, the relation names `less than` / `at least` and the `ValueError` on any other, the sort and dedupe of keyword lists, `letter.strip().lower()`, `keyword.strip()`, `section_spliter.strip()`, `postscript_marker.strip()`, `end_phrase.strip().lower()`, and the `P.S.` / `P.P.S` special patterns.

## tests

`tests/test_ifeval.py`: hand-written pass and fail cases for each of the 21 ids, the loose variants, the no-letter rule, the tokenizer, and a run of every scored instruction of all 541 rows (691 instructions) on dummy answers, so every kwargs set fits its check. Results are in `README.md`.
