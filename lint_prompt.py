#!/usr/bin/env python3
"""Lint a voice agent prompt.

Usage:
    python lint_prompt.py path/to/prompt.md
    python lint_prompt.py templates/closer.md --template      # {{placeholders}} are expected
    python lint_prompt.py prompt.md --max-chars 8000 --min-score 90

Checks:
  - the 10 required sections (fuzzy heading match)
  - red-flag phrases (a line that tells the agent NOT to say it is fine)
  - prompt length
  - {{placeholders}} left unfilled

Prints a score out of 100 with fixes. Exits 1 if the score is under --min-score.
"""
import argparse
import difflib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fill import find_placeholders  # noqa: E402

SECTIONS = [
    ("ROLE AND GOAL", ["role and goal", "role", "goal"]),
    ("OPENING", ["opening", "greeting", "first line"]),
    ("VOICEMAIL AND CALL SCREENING", ["voicemail", "call screening", "answering machine"]),
    ("CONVERSATION RULES", ["conversation rules", "conversation style", "speaking rules"]),
    ("TIME ZONE BEFORE BOOKING", ["time zone", "timezone"]),
    ("CONFIRM BEFORE ACTIONS", ["confirm before", "confirmation"]),
    ("OBJECTION HANDLING", ["objection"]),
    ("OPT OUT AND COMPLIANCE", ["opt out", "do not call", "compliance"]),
    ("TRANSFER AND ESCALATION", ["transfer", "escalation"]),
    ("END OF CALL", ["end of call", "ending the call", "closing the call"]),
]

# (regex, message). A match on a line that also tells the agent never to do it is ignored.
RED_FLAGS = [
    (r"are you still there", 'Never say "are you still there". It sounds robotic and breaks on voicemail.'),
    (r"as an ai language model", 'Remove "as an AI language model". Say you are an AI assistant for the business if asked.'),
    (r"\bguarantee[ds]?\b", "Remove promises like guarantee. The agent must not promise results."),
    (r"\bi promise\b", 'Remove "I promise". The agent must not make promises.'),
    (r"\brisk[- ]free\b", 'Remove "risk free". The agent must not make claims it cannot back up.'),
]
NEGATION = re.compile(r"\b(never|not|don't|dont|do not|avoid|without|remove)\b", re.I)
PLACEHOLDER_PENALTY = 2
PLACEHOLDER_PENALTY_CAP = 20
SECTION_PENALTY = 8
RED_FLAG_PENALTY = 5
LENGTH_PENALTY = 10


def normalize(heading):
    heading = re.sub(r"[^a-z0-9 ]+", " ", heading.lower())
    heading = re.sub(r"^\s*\d+\s*", "", heading)  # drop "1." style numbering
    return " ".join(heading.split())


def headings(text):
    return [normalize(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M)]


def heading_matches(heading, keywords):
    for kw in keywords:
        if kw in heading:
            return True
        if difflib.SequenceMatcher(None, kw, heading).ratio() >= 0.8:
            return True
    return False


def find_sections(text):
    """Return (found, missing) lists of canonical section names."""
    heads = headings(text)
    found, missing = [], []
    for name, keywords in SECTIONS:
        if any(heading_matches(h, keywords) for h in heads):
            found.append(name)
        else:
            missing.append(name)
    return found, missing


def find_red_flags(text):
    """Return a list of (line_number, message) for red-flag phrases."""
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if NEGATION.search(line):
            continue
        for pattern, message in RED_FLAGS:
            if re.search(pattern, line, re.I):
                hits.append((i, message))
    return hits


def lint(text, max_chars=6000, template=False):
    """Return a dict with score, problems (list of strings) and details."""
    score = 100
    problems = []
    found, missing = find_sections(text)
    for name in missing:
        score -= SECTION_PENALTY
        problems.append("Missing section: %s. Add a heading named %s." % (name, name))
    for line_no, message in find_red_flags(text):
        score -= RED_FLAG_PENALTY
        problems.append("Line %d: %s" % (line_no, message))
    chars = len(text)
    if chars > max_chars:
        score -= LENGTH_PENALTY
        problems.append(
            "Prompt is %d characters, over the %d limit. Long prompts cost more and slow the agent. "
            "Cut examples and repeated rules." % (chars, max_chars)
        )
    names = sorted(find_placeholders(text))
    if names and not template:
        score -= min(PLACEHOLDER_PENALTY * len(names), PLACEHOLDER_PENALTY_CAP)
        problems.append(
            "Unfilled placeholders: %s. Run fill.py or replace them." % ", ".join("{{%s}}" % n for n in names)
        )
    return {
        "score": max(score, 0),
        "problems": problems,
        "sections_found": found,
        "sections_missing": missing,
        "chars": chars,
        "placeholders": names,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="Lint a voice agent prompt.")
    p.add_argument("path", help="prompt markdown file")
    p.add_argument("--max-chars", type=int, default=6000, help="warn above this many characters (default 6000)")
    p.add_argument("--min-score", type=int, default=80, help="exit 1 under this score (default 80)")
    p.add_argument("--template", action="store_true", help="treat {{placeholders}} as expected, not as problems")
    args = p.parse_args(argv)

    with open(args.path, encoding="utf-8") as f:
        text = f.read()
    result = lint(text, max_chars=args.max_chars, template=args.template)

    print(args.path)
    print("Sections: %d/10   Characters: %d   Placeholders: %d" % (
        len(result["sections_found"]), result["chars"], len(result["placeholders"])))
    for problem in result["problems"]:
        print("  FIX  " + problem)
    print("Score: %d/100" % result["score"])
    return 1 if result["score"] < args.min_score else 0


if __name__ == "__main__":
    sys.exit(main())
