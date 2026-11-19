"""KpiLib: KPI measurements with statistics (module 4.4)."""
import json
import math
import os
import statistics

from robot.api.deco import keyword, library
from robot.utils import timestr_to_secs

import day2_lte as lab


def percentile(values, p):
    """Nearest-rank percentile (p in 0..100)."""
    if not values:
        raise ValueError("No values to compute a percentile from")
    ordered = sorted(values)
    return ordered[max(math.ceil(p / 100 * len(ordered)) - 1, 0)]


@library(scope="GLOBAL", auto_keywords=False)
class KpiLib:

    @keyword("Run Attach Cycles")
    def run_attach_cycles(self, cycles=40, imsi="001010123456001"):
        """Attach and detach ``cycles`` times. Returns a dict with attempts, successes,
        success_rate (percent), setup_ms (list), median_ms and p95_ms."""
        lab.provision_subscriber(imsi, lab.UE_KEY, "63bfa50ee6523365ff14c1f45f88737d")
        setups, ok = [], 0
        for _ in range(int(cycles)):
            r = lab.attach(imsi, timeout=30.0)
            if r.success:
                ok += 1
                setups.append(r.setup_ms)
            lab.detach(imsi)
        return {"attempts": int(cycles), "successes": ok,
                "success_rate": round(100.0 * ok / int(cycles), 1),
                "setup_ms": setups,
                "median_ms": statistics.median(setups) if setups else None,
                "p95_ms": percentile(setups, 95) if setups else None}

    @keyword("Measure Throughput")
    def measure_throughput(self, direction="DL", duration="10s", warmup="2s", ues=1):
        """Mean Mbit/s after the warm-up seconds are removed."""
        secs, skip = int(timestr_to_secs(duration)), int(timestr_to_secs(warmup))
        samples = lab.throughput_samples(direction, secs, ues=int(ues))
        steady = samples[skip:]
        if not steady:
            raise AssertionError("Duration must be longer than the warm-up period.")
        return round(statistics.mean(steady), 2)

    @keyword("Measure Latency")
    def measure_latency(self, imsi, count=20):
        """Ping ``count`` times. Returns a dict with mean_ms and p95_ms."""
        rtts = lab.ping(imsi, int(count))
        if not rtts:
            raise AssertionError(f"No ping replies for {imsi}. Is the UE attached with an IP?")
        return {"mean_ms": round(statistics.mean(rtts), 1), "p95_ms": percentile(rtts, 95)}

    @keyword("Percentile")
    def percentile_kw(self, values, p=95):
        """Nearest-rank percentile of a list."""
        return percentile([float(v) for v in values], float(p))

    @keyword("Save KPI Summary")
    def save_kpi_summary(self, path, data):
        """Write a dict as JSON (for CI and trend charts)."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path
