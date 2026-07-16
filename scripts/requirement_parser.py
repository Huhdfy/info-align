"""
Semantic Pattern Parser — Info Align Phase 2 (Regex Engine)

Reads Task Context text and applies 6 semantic pattern rules using regex.
Outputs a list of extracted field objects as JSON for downstream LLM phases
(2.5 Quadrant Questioning, 3 Field Reasoning).

Usage:
    python requirement_parser.py -f input.txt
    echo "需要输出CSV文件" | python requirement_parser.py
    python requirement_parser.py -f input.txt --pretty
"""

import re
import json
import sys
import argparse
from typing import Optional


# ────────────────────────────────────────────────────────────
# Sentence splitting
# ────────────────────────────────────────────────────────────

_SENTENCE_RE = re.compile(r'[。！？；\n，,]+')


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]


# ────────────────────────────────────────────────────────────
# Pattern definitions  (name, regex, priority)
# priority: lower = higher precedence when overlapping
# ────────────────────────────────────────────────────────────

_PATTERNS: list[tuple[str, re.Pattern, int]] = [
    # name         regex                                    pri
    ("required",   re.compile(r'需要|必须|请提供|务必'),       1),
    ("default",    re.compile(r'默认|通常|若未指定|一般情况下'), 2),
    ("optional",   re.compile(r'可以|省略|可选|若不需要可'),    3),
    ("constraint", re.compile(r'不要|禁止|不得|切勿|严禁'),     4),
    ("output",     re.compile(r'输出|生成|返回|产出|格式为'),   5),
    ("execution",  re.compile(r'优先|首先|最后|先.*?再'),      6),
]

# Exclusion: "需要/必须" whose subject/target is "你" / "AI" / "您"
# Covers both "你需要" (subject-verb) and "需要你" (verb-object)
_EXCLUDE_REQUIRED_TARGET = re.compile(
    r'(你|AI|您|你们|你方)\s*(需要|必须)|(需要|必须)\s*(你|AI|您|你们|你方)'
)

# Common stop tokens that mark end of field value
_VALUE_STOP = re.compile(r'[,，。！？；\n]|$')


# ────────────────────────────────────────────────────────────
# Core extraction
# ────────────────────────────────────────────────────────────

def extract_fields(text: str) -> list[dict]:
    """
    Main entry point.
    Returns a list of field dicts with keys:
        pattern, key, value, source, sentence, [required, constraint, output, execution]
    """
    sentences = _split_sentences(text)
    fields: list[dict] = []

    for sentence in sentences:
        field = _extract_one(sentence)
        if field:
            fields.append(field)

    return fields


def _extract_one(sentence: str) -> Optional[dict]:
    """Try to extract one field from a sentence.  Returns None if no pattern matches."""

    # ── Exclusion check: required-pattern targeting "你/AI" ──
    if _EXCLUDE_REQUIRED_TARGET.search(sentence):
        active = [p for p in _PATTERNS if p[0] != "required"]
    else:
        active = list(_PATTERNS)

    # Collect all matches with their priority
    candidates: list[tuple[int, str, re.Match]] = []
    for name, pattern_re, priority in active:
        for m in pattern_re.finditer(sentence):
            # Prevent substring double-match (e.g. "先…再" matching inside "首先")
            if _is_subsumed(m, candidates, name):
                continue
            candidates.append((priority, name, m))

    if not candidates:
        return None

    # Keep highest-priority (lowest number) match
    candidates.sort(key=lambda x: x[0])
    best_priority, best_name, best_match = candidates[0]

    # Also collect lower-priority matches as supplementary info
    supplementary = {}
    for pri, name, m in candidates[1:]:
        if name not in supplementary:
            supplementary[name] = _extract_value(sentence, m)

    return _build_field(best_name, sentence, best_match, supplementary)


def _is_subsumed(match: re.Match, existing: list, name: str) -> bool:
    """Check if match span is fully inside an already-matched higher-priority pattern of same type."""
    ms, me = match.span()
    for _, ename, em in existing:
        if ename == name:
            es, ee = em.span()
            if es <= ms and me <= ee and (es < ms or me < ee):
                return True
    return False


# ────────────────────────────────────────────────────────────
# Field builder
# ────────────────────────────────────────────────────────────

def _build_field(
    pattern_name: str,
    sentence: str,
    match: re.Match,
    supplementary: dict,
) -> dict:
    start, end = match.span()
    keyword = match.group(0)

    before = sentence[:start].strip()
    after = sentence[end:].strip()

    key = _derive_key(before, after, keyword)
    value = _extract_value(sentence, match)

    field: dict = {
        "pattern": pattern_name,
        "key": key,
        "source": "parser",
        "sentence": sentence,
    }

    if pattern_name == "required":
        field["required"] = True
        field["value"] = value
    elif pattern_name == "default":
        field["required"] = False
        field["value"] = value or None
    elif pattern_name == "optional":
        field["required"] = False
        field["value"] = None
    elif pattern_name == "constraint":
        field["constraint"] = (after or before).strip() or keyword
    elif pattern_name == "output":
        field["output"] = value or keyword
    elif pattern_name == "execution":
        field["execution"] = keyword

    # Attach supplementary lower-priority pattern hits
    if supplementary:
        field["_supplementary"] = supplementary

    return field


# ────────────────────────────────────────────────────────────
# Key / Value extraction helpers
# ────────────────────────────────────────────────────────────

_KEY_CLEAN = re.compile(r'[的得地了着过之与和及把被让将]')


def _derive_key(before: str, after: str, keyword: str) -> str:
    """Derive a readable field key from surrounding context."""
    # Prefer text before keyword as the topic
    candidate = before or after or ""
    # Clean grammatical particles
    candidate = _KEY_CLEAN.sub('', candidate)
    candidate = candidate.strip()
    if len(candidate) > 30:
        candidate = candidate[:30]
    if not candidate:
        # Fallback: use keyword plus position context
        candidate = f"_{keyword}"
    return candidate


def _extract_value(sentence: str, match: re.Match) -> Optional[str]:
    """Extract the value portion — content after the keyword until a stop token."""
    end = match.end()
    tail = sentence[end:].strip()
    # Trim at stop token (punctuation / line break)
    m_stop = _VALUE_STOP.search(tail)
    if m_stop:
        tail = tail[:m_stop.start()]
    tail = tail.strip()
    return tail if tail else None


# ────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Info Align Phase 2 — Semantic Pattern Parser"
    )
    ap.add_argument("--file", "-f", type=str, help="Input text file (UTF-8)")
    ap.add_argument("--output", "-o", type=str, help="Output JSON file (UTF-8, defaults to stdout)")
    ap.add_argument("--pretty", "-p", action="store_true", help="Pretty-print JSON")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    else:
        # Read stdin as raw bytes then decode as UTF-8 (avoids console codec)
        raw = sys.stdin.buffer.read()
        text = raw.decode("utf-8-sig")

    results = extract_fields(text)
    indent = 2 if args.pretty else None
    output = json.dumps(results, ensure_ascii=False, indent=indent)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output + "\n")
    else:
        sys.stdout.buffer.write(output.encode("utf-8") + b"\n")


if __name__ == "__main__":
    main()
