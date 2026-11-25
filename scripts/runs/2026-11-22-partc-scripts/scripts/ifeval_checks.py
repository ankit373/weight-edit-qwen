"""IFEval instruction checks, stdlib port (PROTOCOL.md section 3). no downloaded code is imported.

ported from the IFEval checker (google-research instruction_following_eval, Apache-2.0), read as
text in the lm-eval copy lm_eval/tasks/ifeval/{instructions.py,utils.py} (commit c562a075, local
clone). only the 21 non-length instruction ids in data/partc/ifeval are ported. every change from
the official checker is listed in ../DEVIATIONS.md:
  - langdetect -> fastText lid.176.bin (language:response_language, change_case:english_capital,
    change_case:english_lowercase); loaded lazily, so the other checks stay stdlib only
  - nltk.word_tokenize -> word_tokenize() below (change_case:capital_word_frequency)
"""
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LID = os.path.abspath(os.path.join(HERE, "..", "..", "2026-11-05-gate1-baseline", "scoring_workdir", "lid.176.bin"))
COMPARISON = ("less than", "at least")  # _COMPARISON_RELATION
CONSTRAINED = ("My answer is yes.", "My answer is no.", "My answer is maybe.")  # _CONSTRAINED_RESPONSE_OPTIONS

_lid = None


class DetectFailed(Exception):
    """stand-in for langdetect.LangDetectException: the text has no letter at all."""


def detect(text):
    """top-1 fastText lid.176 label (langdetect.detect stand-in). no score threshold."""
    global _lid
    if not any(ch.isalpha() for ch in text):
        raise DetectFailed(text)
    if _lid is None:
        import fasttext  # score env only
        _lid = fasttext.load_model(LID)
    (label,), _ = _lid.predict(" ".join(text.split()))  # fastText reads one line
    return label.removeprefix("__label__")


# clitics split off by the Penn Treebank rules nltk.word_tokenize applies
_CLITIC = re.compile(r"(?i)^(.+?)('s|'m|'d|'ll|'re|'ve|n't)$")
_EDGE = "\"'`()[]{}<>,;:!?.*_~#«»“”‘’…"


def word_tokenize(text):
    """nltk.word_tokenize stand-in: whitespace split, edge punctuation split off, clitics split.
    hyphens and inner dots stay inside a word, as in nltk."""
    out = []
    for tok in text.split():
        lead = []
        while tok and tok[0] in _EDGE:
            lead.append(tok[0])
            tok = tok[1:]
        trail = []
        while tok and tok[-1] in _EDGE:
            trail.append(tok[-1])
            tok = tok[:-1]
        out.extend(lead)
        if tok:
            m = _CLITIC.match(tok)
            out.extend([m.group(1), m.group(2)] if m else [tok])
        out.extend(reversed(trail))
    return out


def _rel(n, relation, threshold):
    if relation == COMPARISON[0]:
        return n < threshold
    return n >= threshold


def _need_rel(relation):
    if relation not in COMPARISON:
        raise ValueError(f"relation {relation} not in {COMPARISON}")


# ---- one function per instruction id: f(value, **kwargs) -> bool, same logic as check_following

def keywords_existence(value, keywords):
    for keyword in sorted(keywords):
        if not re.search(keyword, value, flags=re.IGNORECASE):
            return False
    return True


def keywords_frequency(value, keyword, frequency, relation):
    _need_rel(relation)
    n = len(re.findall(keyword.strip(), value, flags=re.IGNORECASE))
    return _rel(n, relation, frequency)


def keywords_forbidden_words(value, forbidden_words):
    for word in sorted(set(forbidden_words)):
        if re.search(r"\b" + word + r"\b", value, flags=re.IGNORECASE):
            return False
    return True


def keywords_letter_frequency(value, letter, let_frequency, let_relation):
    _need_rel(let_relation)
    letter = letter.strip().lower()
    letters = collections.Counter(value.lower())
    return _rel(letters[letter], let_relation, let_frequency)


def language_response_language(value, language):
    try:
        return detect(value) == language
    except DetectFailed:
        return True  # official: LangDetectException -> counted as followed


def detectable_content_number_placeholders(value, num_placeholders):
    return len(re.findall(r"\[.*?\]", value)) >= num_placeholders


def detectable_content_postscript(value, postscript_marker):
    marker = postscript_marker.strip()
    value = value.lower()
    if marker == "P.P.S":
        pattern = r"\s*p\.\s?p\.\s?s.*$"
    elif marker == "P.S.":
        pattern = r"\s*p\.\s?s\..*$"
    else:
        pattern = r"\s*" + marker.lower() + r".*$"
    return bool(re.findall(pattern, value, flags=re.MULTILINE))


def detectable_format_number_bullet_lists(value, num_bullets):
    a = re.findall(r"^\s*\*[^\*].*$", value, flags=re.MULTILINE)
    b = re.findall(r"^\s*-.*$", value, flags=re.MULTILINE)
    return len(a) + len(b) == num_bullets


def detectable_format_constrained_response(value):
    value = value.strip()
    return any(c in value for c in CONSTRAINED)


def detectable_format_number_highlighted_sections(value, num_highlights):
    n = 0
    for h in re.findall(r"\*[^\n\*]*\*", value):
        if h.strip("*").strip():
            n += 1
    for h in re.findall(r"\*\*[^\n\*]*\*\*", value):
        if h.removeprefix("**").removesuffix("**").strip():
            n += 1
    return n >= num_highlights


def detectable_format_multiple_sections(value, section_spliter, num_sections):
    pattern = r"\s?" + section_spliter.strip() + r"\s?\d+\s?"
    return len(re.split(pattern, value)) - 1 >= num_sections


def detectable_format_json_format(value):
    value = (value.strip().removeprefix("```json").removeprefix("```Json").removeprefix("```JSON")
             .removeprefix("```").removesuffix("```").strip())
    try:
        json.loads(value)
    except ValueError:
        return False
    return True


def detectable_format_title(value):
    titles = re.findall(r"<<[^\n]+>>", value)
    return any(t.lstrip("<").rstrip(">").strip() for t in titles)


def combination_two_responses(value):
    valid = []
    parts = value.split("******")
    for i, part in enumerate(parts):
        if not part.strip():
            if i != 0 and i != len(parts) - 1:
                return False
        else:
            valid.append(part)
    return len(valid) == 2 and valid[0].strip() != valid[1].strip()


def combination_repeat_prompt(value, prompt_to_repeat):
    return value.strip().lower().startswith(prompt_to_repeat.strip().lower())


def startend_end_checker(value, end_phrase):
    value = value.strip().strip('"').lower()
    return value.endswith(end_phrase.strip().lower())


def startend_quotation(value):
    value = value.strip()
    return len(value) > 1 and value[0] == '"' and value[-1] == '"'


def change_case_capital_word_frequency(value, capital_frequency, capital_relation):
    _need_rel(capital_relation)
    n = sum(1 for w in word_tokenize(value) if w.isupper())
    return _rel(n, capital_relation, capital_frequency)


def change_case_english_capital(value):
    try:
        # lower-cased for the language id only: fastText is unreliable on all-caps text (DEVIATIONS.md)
        return value.isupper() and detect(value.lower()) == "en"
    except DetectFailed:
        return True


def change_case_english_lowercase(value):
    try:
        return value.islower() and detect(value) == "en"
    except DetectFailed:
        return True


def punctuation_no_comma(value):
    return not re.search(r"\,", value)


CHECKS = {
    "keywords:existence": keywords_existence,
    "keywords:frequency": keywords_frequency,
    "keywords:forbidden_words": keywords_forbidden_words,
    "keywords:letter_frequency": keywords_letter_frequency,
    "language:response_language": language_response_language,
    "detectable_content:number_placeholders": detectable_content_number_placeholders,
    "detectable_content:postscript": detectable_content_postscript,
    "detectable_format:number_bullet_lists": detectable_format_number_bullet_lists,
    "detectable_format:constrained_response": detectable_format_constrained_response,
    "detectable_format:number_highlighted_sections": detectable_format_number_highlighted_sections,
    "detectable_format:multiple_sections": detectable_format_multiple_sections,
    "detectable_format:json_format": detectable_format_json_format,
    "detectable_format:title": detectable_format_title,
    "combination:two_responses": combination_two_responses,
    "combination:repeat_prompt": combination_repeat_prompt,
    "startend:end_checker": startend_end_checker,
    "startend:quotation": startend_quotation,
    "change_case:capital_word_frequency": change_case_capital_word_frequency,
    "change_case:english_capital": change_case_english_capital,
    "change_case:english_lowercase": change_case_english_lowercase,
    "punctuation:no_comma": punctuation_no_comma,
}


def clean_kwargs(kw):
    """utils.py: drop None (and other falsy) values before build_description."""
    return {k: v for k, v in kw.items() if v}


def loose_variants(response):
    """utils.test_instruction_following_loose: the 8 response variants, in order."""
    r = response.split("\n")
    first = "\n".join(r[1:]).strip()
    last = "\n".join(r[:-1]).strip()
    both = "\n".join(r[1:-1]).strip()
    return [response, response.replace("*", ""), first, last, both,
            first.replace("*", ""), last.replace("*", ""), both.replace("*", "")]


def follows(instruction_id, kwargs, response, loose=False):
    check = CHECKS[instruction_id]
    kw = clean_kwargs(kwargs)
    for v in (loose_variants(response) if loose else [response]):
        if v.strip() and check(v, **kw):
            return True
    return False
