"""Plain Python checks of the CI tools (gate and lint). Run:  python -m unittest discover tests_py -v"""
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PY = sys.executable


def run(*args):
    return subprocess.run([PY, *args], cwd=ROOT, capture_output=True, text=True)


def make_output(folder, tests):
    """Run a tiny suite with the given (name, tags, passes) tests and return its output.xml."""
    body = "*** Test Cases ***\n"
    for name, tags, ok in tests:
        body += f"{name}\n    [Tags]    {'    '.join(tags)}\n    {'No Operation' if ok else 'Fail    boom'}\n"
    suite = os.path.join(folder, "t.robot")
    with open(suite, "w") as f:
        f.write(body)
    subprocess.run([PY, "-m", "robot", "--output", "o.xml", "--log", "NONE", "--report", "NONE",
                    "--outputdir", folder, suite], capture_output=True)
    return os.path.join(folder, "o.xml")


class Gate(unittest.TestCase):
    def test_pass_when_all_pass(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run("ci/gate.py", make_output(d, [("A", ["x"], True)])).returncode, 0)

    def test_fail_when_a_gated_test_fails(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run("ci/gate.py", make_output(d, [("A", ["x"], True), ("B", ["x"], False)])).returncode, 1)

    def test_quarantined_failure_does_not_fail_the_gate(self):
        with tempfile.TemporaryDirectory() as d:
            r = run("ci/gate.py", make_output(d, [("A", ["x"], True), ("B", ["quarantine"], False)]))
            self.assertEqual(r.returncode, 0)
            self.assertIn("Quarantined", r.stdout)

    def test_missing_file_is_not_a_pass(self):
        self.assertEqual(run("ci/gate.py", "does/not/exist.xml").returncode, 2)


class Lint(unittest.TestCase):
    def test_clean_suites(self):
        self.assertEqual(run("tools/lint_suite.py", "suites").returncode, 0)

    def test_bad_demo_is_caught(self):
        r = run("tools/lint_suite.py", "demos/lint_bad.robot")
        self.assertEqual(r.returncode, 1)
        for rule in ("DOC", "REQ", "TYPE", "SLEEP", "DATA"):
            self.assertIn(f" {rule} ", r.stdout)


if __name__ == "__main__":
    unittest.main()
