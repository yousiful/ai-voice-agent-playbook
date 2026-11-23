"""Tests for lint_prompt.py and fill.py. No network, no credentials.

Run with `python -m pytest tests/` or `python tests/test_lint.py`.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import fill  # noqa: E402
import lint_prompt  # noqa: E402

TEMPLATES = sorted(glob.glob(os.path.join(ROOT, "templates", "*.md")))
VARS = os.path.join(ROOT, "examples", "vars.example.json")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_four_templates_exist():
    names = {os.path.basename(p) for p in TEMPLATES}
    assert names == {"appointment-setter.md", "closer.md", "receptionist.md", "reactivation.md"}


def test_every_template_scores_100():
    for path in TEMPLATES:
        result = lint_prompt.lint(read(path), template=True)
        assert result["score"] == 100, (path, result["problems"])


def test_every_template_fills_and_scores_100():
    variables = json.loads(read(VARS))
    for path in TEMPLATES:
        filled = fill.fill(read(path), variables)
        assert "{{" not in filled
        result = lint_prompt.lint(filled)
        assert result["score"] == 100, (path, result["problems"])


def test_unfilled_placeholders_are_penalized_unless_template_mode():
    text = read(TEMPLATES[0])
    assert lint_prompt.lint(text)["score"] < 100
    assert lint_prompt.lint(text, template=True)["score"] == 100


def test_missing_section_is_found():
    text = read(os.path.join(ROOT, "templates", "closer.md")).replace("## OBJECTION HANDLING", "## Notes")
    result = lint_prompt.lint(text, template=True)
    assert result["sections_missing"] == ["OBJECTION HANDLING"]
    assert result["score"] == 92


def test_fuzzy_heading_match():
    text = "## 1. Role & Goal\n## Greeting\n## Voice mail and call screening\n"
    found, _ = lint_prompt.find_sections(text)
    assert "ROLE AND GOAL" in found
    assert "OPENING" in found
    assert "VOICEMAIL AND CALL SCREENING" in found


def test_red_flags_detected():
    text = 'Say "are you still there?" when quiet.\nWe guarantee results.\nAs an AI language model, I help.\n'
    hits = lint_prompt.find_red_flags(text)
    assert len(hits) == 3


def test_red_flag_ignored_when_told_never_to_say_it():
    text = 'Never say "are you still there" to a machine.\nNever promise or guarantee results.\n'
    assert lint_prompt.find_red_flags(text) == []


def test_length_warning():
    text = read(TEMPLATES[0])
    result = lint_prompt.lint(text, max_chars=1000, template=True)
    assert result["score"] == 90
    assert any("characters" in p for p in result["problems"])


def test_exit_code_under_threshold():
    path = os.path.join(ROOT, "tests", "_bad_prompt.tmp.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Bot\nSay are you still there. We guarantee it.\n")
    try:
        assert lint_prompt.main([path]) == 1
    finally:
        os.remove(path)


def test_exit_code_ok_for_template():
    assert lint_prompt.main([TEMPLATES[0], "--template"]) == 0


def test_fill_replaces_and_ignores_extra_keys():
    out = fill.fill("Hi {{ name }}, from {{biz}}.", {"name": "Sam", "biz": "Acme Roofing", "unused": "x"})
    assert out == "Hi Sam, from Acme Roofing."


def test_fill_errors_on_missing_vars():
    try:
        fill.fill("Hi {{name}} {{city}}", {"name": "Sam"})
    except fill.MissingVars as e:
        assert e.names == ["city"]
    else:
        raise AssertionError("expected MissingVars")


def test_no_em_dashes_anywhere():
    paths = TEMPLATES + glob.glob(os.path.join(ROOT, "*.md")) + glob.glob(os.path.join(ROOT, "docs", "*"))
    for path in paths:
        assert chr(0x2014) not in read(path), path


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS " + name)
            except Exception as e:  # noqa: BLE001
                failures += 1
                print("FAIL %s: %r" % (name, e))
    print("%d failed" % failures if failures else "all passed")
    sys.exit(1 if failures else 0)
