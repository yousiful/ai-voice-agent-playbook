#!/usr/bin/env python3
"""Fill {{placeholders}} in a prompt template from a JSON file.

Usage:
    python fill.py templates/closer.md examples/vars.example.json > out/closer.md

Exits 1 and prints the missing names to stderr if any placeholder has no value.
Extra keys in the JSON file are ignored.
"""
import json
import re
import sys

PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


class MissingVars(Exception):
    def __init__(self, names):
        self.names = sorted(names)
        super().__init__("missing variables: " + ", ".join(self.names))


def find_placeholders(text):
    """Return the set of placeholder names used in text."""
    return set(PLACEHOLDER.findall(text))


def fill(text, variables):
    """Replace every {{name}} with variables[name]. Raise MissingVars if any are absent."""
    missing = [n for n in find_placeholders(text) if n not in variables]
    if missing:
        raise MissingVars(missing)
    return PLACEHOLDER.sub(lambda m: str(variables[m.group(1)]), text)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: python fill.py template.md vars.json > out.md", file=sys.stderr)
        return 2
    template_path, vars_path = argv
    with open(template_path, encoding="utf-8") as f:
        text = f.read()
    with open(vars_path, encoding="utf-8") as f:
        variables = json.load(f)
    try:
        result = fill(text, variables)
    except MissingVars as e:
        print("error: " + str(e), file=sys.stderr)
        return 1
    sys.stdout.buffer.write(result.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
