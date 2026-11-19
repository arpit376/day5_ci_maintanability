"""EvidenceLib: attach evidence to a test (module 5.1).

Called from the Test Teardown, which runs even when the test failed.
Creates   <outputdir>/evidence/<test-name>_<time>/   containing
    lab.log          core / eNodeB / UE log of the lab
    capture.json     the capture, when one is running or was just stopped (simulated lab)
    kpi_summary.txt  KPI files written in this run, if any
    versions.txt     environment and version information
    result.txt       test name, status, message, tags
and logs a link to the folder in log.html (html=True).
"""
import glob
import os
import platform
import re
import sys
import time

from robot.api import logger
from robot.api.deco import keyword, library
from robot.libraries.BuiltIn import BuiltIn

import capture_view
import day2_lte as lab


def safe_name(text, limit=60):
    """File-system safe name: letters, digits, dash, underscore."""
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")[:limit] or "test"


@library(scope="GLOBAL", auto_keywords=False)
class EvidenceLib:

    @keyword("Collect Evidence")
    def collect_evidence(self, always=False):
        """Copy the evidence for the current test into its own folder.

        By default only a FAILED test gets a folder ("a failure without evidence is a rerun").
        Pass ``always=True`` (or set ``${EVIDENCE_ALWAYS}`` to True) to keep it for passes too.
        Returns the folder path, or ``None`` when nothing was collected.
        """
        bi = BuiltIn()
        status = bi.get_variable_value("${TEST STATUS}", "")
        keep_all = str(bi.get_variable_value("${EVIDENCE_ALWAYS}", "False")).lower() in ("true", "1", "yes")
        if status != "FAIL" and not (always or keep_all):
            return None

        name = bi.get_variable_value("${TEST NAME}", "suite")
        outdir = bi.get_variable_value("${OUTPUT DIR}", ".")
        folder = os.path.join(outdir, "evidence", f"{safe_name(name)}_{time.strftime('%Y%m%d-%H%M%S')}")
        os.makedirs(folder, exist_ok=True)

        lab.save_logs(os.path.join(folder, "lab.log"))
        self._copy_captures(outdir, folder)
        self._copy_kpi(outdir, folder)
        self._write_versions(folder)
        with open(os.path.join(folder, "result.txt"), "w") as f:
            f.write(f"test:    {name}\nstatus:  {status}\n"
                    f"message: {bi.get_variable_value('${TEST MESSAGE}', '')}\n"
                    f"tags:    {', '.join(bi.get_variable_value('@{TEST TAGS}', []))}\n")

        rel = os.path.relpath(folder, outdir)
        logger.info(f'Evidence for "{name}": <a href="{rel}/lab.log">lab.log</a> | '
                    f'<a href="{rel}/versions.txt">versions</a> | '
                    f'<a href="{rel}/result.txt">result</a> (folder: {rel})', html=True)
        return folder

    # ---- helpers ------------------------------------------------------------
    @staticmethod
    def _copy_captures(outdir, folder):
        """Write the running capture (if any) and copy captures stopped by the test."""
        if lab._state.get("capturing") or lab._state.get("events"):
            lab.capture_stop(os.path.join(folder, "capture.json"))
        for path in glob.glob(os.path.join(outdir, "captures", "*.json")):
            with open(path, "rb") as src, open(os.path.join(folder, os.path.basename(path)), "wb") as dst:
                dst.write(src.read())
        for path in glob.glob(os.path.join(folder, "*.json")):      # Wireshark-style page for each capture
            try:
                capture_view.build_html(path)
            except Exception:
                pass

    @staticmethod
    def _copy_kpi(outdir, folder):
        files = sorted(glob.glob(os.path.join(outdir, "kpi_*.json")))
        if files:
            with open(os.path.join(folder, "kpi_summary.txt"), "w") as out:
                for path in files:
                    out.write(f"== {os.path.basename(path)}\n")
                    with open(path) as f:
                        out.write(f.read() + "\n")

    @staticmethod
    def _write_versions(folder):
        import robot
        lines = [f"time:       {time.strftime('%Y-%m-%d %H:%M:%S')}",
                 f"host:       {platform.node()}",
                 f"python:     {sys.version.split()[0]}",
                 f"robot:      {robot.__version__}",
                 f"LAB_FAULT:  {os.environ.get('LAB_FAULT', '') or 'none'}",
                 f"LAB_SEED:   {os.environ.get('LAB_SEED', '42')}",
                 "lab:        simulated (day2_lte.py). On the real VM add: Open5GS, OAI and tshark versions here."]
        with open(os.path.join(folder, "versions.txt"), "w") as f:
            f.write("\n".join(lines) + "\n")
