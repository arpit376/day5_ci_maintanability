#!/usr/bin/env python3
"""Suite lint (module 5.4): keep a growing suite maintainable.

    python tools/lint_suite.py suites          (checks every .robot file below the folder)

Rules, one line each when broken:
  DOC    every test has [Documentation]
  REQ    every test carries a requirement tag REQ-...            (traceability)
  TYPE   every test carries a type tag: smoke functional kpi long negative demo stability
  SLEEP  no 'Sleep' in a test or keyword: wait on state, not on time
  DATA   no hard-coded 15-digit IMSI or IP address in a test: use the variable file
Exit code 1 when anything is found, so it can run in CI before the tests.
"""
import os
import re
import sys

from robot.api import get_model
from robot.parsing import ModelVisitor

TYPE_TAGS = {"smoke", "functional", "kpi", "long", "negative", "demo", "stability", "capacity", "sweep"}
IMSI_RE = re.compile(r"(?<!\d)\d{15}(?!\d)")
IP_RE = re.compile(r"(?<!\d)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?!\d)")
ALLOWED_SLEEP = ("Hold Subscriber",)         # a named stand-in for traffic, see 10_parallel_attach


class Lint(ModelVisitor):
    def __init__(self, path):
        self.path, self.problems, self.suite_tags, self.keyword, self.templated = path, [], set(), None, False

    def add(self, line, rule, text):
        self.problems.append(f"{self.path}:{line}: {rule} {text}")

    def visit_TestTags(self, node):
        self.suite_tags |= set(node.values)

    visit_ForceTags = visit_DefaultTags = visit_TestTags

    def visit_TestTemplate(self, node):
        self.templated = True          # data rows of a template: documented once, in the keyword

    def visit_TestCase(self, node):
        has_doc, tags, body = False, set(self.suite_tags), []
        for item in node.body:
            kind = type(item).__name__
            if kind == "Documentation":
                has_doc = True
            elif kind == "Tags":
                tags |= set(item.values)
            else:
                body.append(item)
        line = node.lineno
        if not has_doc and not self.templated:
            self.add(line, "DOC", f"test '{node.name}' has no [Documentation]")
        if not any(t.startswith("REQ-") for t in tags):
            self.add(line, "REQ", f"test '{node.name}' has no REQ-... tag")
        if not tags & TYPE_TAGS:
            self.add(line, "TYPE", f"test '{node.name}' has no type tag ({', '.join(sorted(TYPE_TAGS))})")
        for item in body:
            self._check_body(item, node.name)

    def _check_body(self, item, owner):
        tokens = list(getattr(item, "tokens", []) or [])
        header = getattr(item, "header", None)          # FOR / IF / TRY / WHILE blocks
        if header is not None:
            tokens += header.tokens
        for tok in tokens:
            if tok.type == "KEYWORD" and tok.value.lower() == "sleep" and self.keyword not in ALLOWED_SLEEP:
                self.add(tok.lineno, "SLEEP", f"'Sleep' in '{owner}': wait on state, not on time")
            if tok.type in ("ARGUMENT", "KEYWORD", "ASSIGN") and "${" not in tok.value:
                if IMSI_RE.search(tok.value):
                    self.add(tok.lineno, "DATA", f"hard-coded IMSI in '{owner}': move it to env/labNN.py")
                elif IP_RE.search(tok.value):
                    self.add(tok.lineno, "DATA", f"hard-coded IP in '{owner}': move it to env/labNN.py")
        for sub in list(getattr(item, "body", []) or []) + ([item.next] if getattr(item, "next", None) else []):
            self._check_body(sub, owner)


def lint_file(path):
    model = get_model(path)
    lint = Lint(path)
    lint.visit(model)
    # Sleep inside keywords is checked with the same rule
    class KwSleep(ModelVisitor):
        def visit_Keyword(self, kw):
            lint.keyword = kw.name
            for item in kw.body:
                if type(item).__name__ not in ("Documentation", "Arguments", "Tags", "Return",
                                               "Teardown", "Timeout", "Setup", "ReturnSetting"):
                    lint._check_body(item, kw.name)
            lint.keyword = None
    KwSleep().visit(model)
    return lint.problems


def main(argv):
    roots = argv or ["suites"]
    files = []
    for root in roots:
        if os.path.isfile(root):
            files.append(root)
        for base, _, names in os.walk(root):
            files += [os.path.join(base, n) for n in sorted(names) if n.endswith(".robot")]
    problems = []
    for f in sorted(files):
        problems += lint_file(f)
    for p in problems:
        print(p)
    print(f"\nlint: {len(files)} files, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
