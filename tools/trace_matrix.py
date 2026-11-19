"""Requirement-to-result matrix from Robot output files (Day 4 and Day 5).

    python tools/trace_matrix.py results/full/output.xml [more output.xml ...]

Reads tags like REQ-ATTACH-01 from the tests, joins them with data/requirements.csv
and prints a markdown table. Requirements with no test are listed as GAPS.
Exit code 0 always: this is a report, not a gate.
"""
import csv
import os
import sys

from robot.api import ExecutionResult, ResultVisitor


class Collect(ResultVisitor):
    def __init__(self):
        self.rows = {}          # req -> list of (test name, status)

    def visit_test(self, test):
        for tag in test.tags:
            if tag.upper().startswith("REQ-"):
                self.rows.setdefault(tag.upper(), []).append((test.name, test.status))


def main(paths):
    if not paths:
        sys.exit(__doc__)
    c = Collect()
    for p in paths:
        ExecutionResult(p).visit(c)
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "data", "requirements.csv")) as f:
        reqs = list(csv.DictReader(f))
    print("| Requirement | Description | Tests | Result |")
    print("|---|---|---|---|")
    gaps = []
    for r in reqs:
        tests = c.rows.get(r["id"], [])
        if not tests:
            gaps.append(r["id"])
            print(f"| {r['id']} | {r['description']} | - | NO TEST |")
            continue
        status = "PASS" if all(s == "PASS" for _, s in tests) else "FAIL"
        print(f"| {r['id']} | {r['description']} | {'; '.join(n for n, _ in tests)} | {status} |")
    unknown = sorted(set(c.rows) - {r["id"] for r in reqs})
    print()
    print(f"Coverage: {len(reqs) - len(gaps)}/{len(reqs)} requirements have at least one test.")
    if gaps:
        print("GAPS (no test traced): " + ", ".join(gaps))
    if unknown:
        print("Tags without a requirement: " + ", ".join(unknown))


if __name__ == "__main__":
    main(sys.argv[1:])
