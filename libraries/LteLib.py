"""LteLib: procedure keywords on top of the Day 2 code (built on Day 3).

Design rules (Day 3, slide 31): one job per keyword, return data, every wait has a
timeout, explain failures.
"""
import os
from collections import Counter

from robot.api import logger
from robot.api.deco import keyword, library
from robot.utils import timestr_to_secs

import day2_lte as lab

DEFAULT_OPC = "63bfa50ee6523365ff14c1f45f88737d"


def _truthy(value):
    return str(value).lower() in ("true", "1", "yes")


@library(scope="SUITE", auto_keywords=False)
class LteLib:
    def __init__(self):
        self._last = {}

    # ---- housekeeping ----------------------------------------------------
    @keyword("Start Core Network")
    def start_core_network(self):
        """Start MME, HSS, S-GW and P-GW."""
        lab.start_core()

    @keyword("Start eNodeB")
    def start_enodeb(self, config="enb.conf"):
        """Start the eNodeB with ``config``."""
        return lab.start_enb(config)

    @keyword("Stop Network Elements")
    def stop_network_elements(self):
        """Stop everything. Safe to call twice."""
        lab.stop_all()

    @keyword("Clear UE State")
    def clear_ue_state(self):
        """Forget attached UEs so the next test starts clean."""
        lab.reset_ue_state()
        self._last.clear()

    @keyword("Set Cell Bandwidth")
    def set_cell_bandwidth(self, mhz):
        """Set the cell bandwidth (5, 10, 15 or 20 MHz). Returns the PRB count."""
        return lab.set_bandwidth(int(mhz))

    @keyword("Save Artefacts")
    def save_artefacts(self, folder):
        """Write the lab log to ``folder`` and link it from the Robot log."""
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "lab.log")
        lab.save_logs(path)
        logger.info(f'<a href="{path}">lab.log</a>', html=True)
        return path

    @keyword("Inject Fault")
    def inject_fault(self, name="none"):
        """Switch a simulated fault on (see day2_lte.py). ``none`` switches it off."""
        os.environ["LAB_FAULT"] = "" if name == "none" else name
        logger.info(f"LAB_FAULT={os.environ['LAB_FAULT'] or 'none'}")

    # ---- subscribers and attach -------------------------------------------
    @keyword("Provision Subscriber")
    def provision_subscriber(self, imsi, key, opc):
        """Create the subscriber in the HSS and return its record."""
        return lab.provision_subscriber(imsi, key, opc)

    @keyword("Provision Subscribers")
    def provision_subscribers(self, count=10, start="001010123457000",
                              key=lab.UE_KEY, opc=DEFAULT_OPC):
        """Provision ``count`` consecutive subscribers and return their IMSIs."""
        imsis = [str(int(start) + i).zfill(15) for i in range(int(count))]
        for imsi in imsis:
            lab.provision_subscriber(imsi, key, opc)
        return imsis

    @keyword("Attach UE")
    def attach_ue(self, imsi, timeout="30s", expect_failure=False):
        """Attach one UE and return an AttachResult.

        ``timeout`` accepts Robot time strings. With ``expect_failure=True`` a
        rejected attach is returned instead of raised."""
        seconds = float(timestr_to_secs(timeout))
        result = lab.attach(imsi, timeout=seconds)
        self._last[imsi] = result
        if not result.success and not _truthy(expect_failure):
            logger.info(f"status={result.status} cause={result.reject_cause}")
            logger.info(lab.tail(40))
            raise AssertionError(
                f"UE {imsi} did not attach: {result.status}, cause={result.reject_cause}. "
                f"See the lab.log artefact.")
        return result

    @keyword("Attach UEs")
    def attach_ues(self, imsis, timeout="60s"):
        """Attach several UEs and return the list of AttachResults (never raises)."""
        return [self.attach_ue(imsi, timeout, expect_failure=True) for imsi in imsis]

    @keyword("Get Attach Result")
    def get_attach_result(self, imsi):
        """Return the last AttachResult of ``imsi``."""
        if imsi not in self._last:
            raise AssertionError(f"No attach was run for {imsi}")
        return self._last[imsi]

    @keyword("Detach UE")
    def detach_ue(self, imsi):
        """Detach the UE."""
        lab.detach(imsi)

    # ---- bearer, idle, TAU --------------------------------------------------
    @keyword("Bearer Should Exist")
    def bearer_should_exist(self, imsi):
        """Fail unless a default bearer exists. Returns the bearer (ip, ebi, teids)."""
        if not lab.bearer_exists(imsi):
            raise AssertionError(f"No default bearer for {imsi}. Check the S11 session and the P-GW.")
        return lab.get_bearer(imsi)

    @keyword("Bearer Should Not Exist")
    def bearer_should_not_exist(self, imsi):
        """Fail if a default bearer exists."""
        if lab.bearer_exists(imsi):
            raise AssertionError(f"A bearer exists for {imsi} but none was expected")

    @keyword("Go Idle")
    def go_idle(self, imsi):
        """Release the radio connection (UE goes idle, bearer is kept)."""
        lab.go_idle(imsi)

    @keyword("Service Request")
    def service_request(self, imsi, downlink_data=True):
        """Bring an idle UE back. Returns a dict: status, paging, bearer_restored."""
        return lab.service_request(imsi, _truthy(downlink_data))

    @keyword("Tracking Area Update")
    def tracking_area_update(self, imsi):
        """Run a TAU. Returns a dict with status."""
        return lab.tau(imsi)

    # ---- multi UE -------------------------------------------------------------
    @keyword("All IP Addresses Should Be Unique")
    def all_ip_addresses_should_be_unique(self, results):
        """Fail if two UEs share an IP, naming the duplicates."""
        counts = Counter(r.ip for r in results)
        dups = sorted(ip for ip, n in counts.items() if n > 1)
        if dups:
            raise AssertionError(f"Duplicate IP addresses: {dups}. Check P-GW IP pool allocation.")

    @keyword("Ping Through Tunnel")
    def ping_through_tunnel(self, imsi, count=2):
        """Send pings from the UE. Returns the RTTs in ms (empty list if no bearer)."""
        return lab.ping(imsi, int(count))
