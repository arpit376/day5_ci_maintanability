"""Stand-in for your Day 2 code: a simulated LTE lab with enough behaviour for Day 4.

On the real lab VM replace the function bodies with your Day 2 code (subprocess,
paramiko, requests, tshark, iperf3, ping). Keep the names and the AttachResult fields.

Faults (set LAB_FAULT in the shell, or use the 'Inject Fault' keyword):
    no_ip          attach works but no IP is allocated          (product defect)
    dup_ip         two UEs get the same IP                      (product defect)
    bad_order      Security Mode Command arrives after Attach Accept
    erab_mismatch  E-RAB ID differs from the EPS bearer ID
    teid_mismatch  downlink GTP-U uses another TEID than the setup
    low_tput       throughput is 60% too low
    high_latency   +60 ms on every ping
    flaky          15% of attaches are rejected at random
    slow / core_down   attach times out                         (environment)
Other: LAB_MAX_UES (default 32) is the number of UEs the VM can hold.
       LAB_SEED (default 42) seeds the random numbers: the same seed repeats a run exactly,
       a different seed gives a different 'flaky' pattern (Day 5, module 5.4).
"""
import json
import os
import random
import time
from dataclasses import dataclass
from typing import Optional

UE_KEY = "00112233445566778899aabbccddeeff"   # key stored on the UE SIM
EMM_UNKNOWN_IMSI = 8
EMM_MAC_FAILURE = 20
EMM_NETWORK_FAILURE = 17
EBI = 5                                        # default EPS bearer ID
PRB_PER_MHZ = {5: 25, 10: 50, 15: 75, 20: 100}
MBPS_PER_PRB = 0.72                            # SISO, 64QAM, simulated


@dataclass
class AttachResult:
    imsi: str
    status: str                      # ATTACHED, REJECTED or TIMEOUT
    cause: Optional[int] = None
    ip: str = ""
    setup_ms: int = 0

    @property
    def success(self):
        return self.status == "ATTACHED"

    @property
    def reject_cause(self):
        return self.cause


def _fresh():
    return {"core": False, "enb": False, "subs": {}, "bearers": {}, "idle": set(),
            "log": [], "next_ip": 2, "n": 0, "events": [], "capturing": False,
            "clock": 0.0, "rng": random.Random(42), "prb": 50}


_state = _fresh()


def fault():
    return os.environ.get("LAB_FAULT", "")


def _log(line):
    _state["log"].append(f"{time.strftime('%H:%M:%S')} {line}")


def _ev(proto, msg, nas="", **extra):
    if _state["capturing"]:
        _state["clock"] += 0.012
        _state["events"].append(dict(t=round(_state["clock"], 3), proto=proto, msg=msg,
                                     nas_type=nas, **extra))


# ---- network control -------------------------------------------------------
def start_core():
    _state["core"] = True
    _state["prb"] = 50
    _state["rng"] = random.Random(int(os.environ.get("LAB_SEED", "42")))
    _log("[core] MME, HSS, S-GW, P-GW started")


def start_enb(config="enb.conf"):
    _state["enb"] = True
    _log(f"[enb] eNodeB started with {config}")
    return {"name": "enb", "config": config}


def stop_all():
    _state.update(core=False, enb=False)
    _state["bearers"].clear()
    _state["idle"].clear()
    _log("[core] all elements stopped")


def reset_ue_state():
    _state["subs"].clear()
    _state["bearers"].clear()
    _state["idle"].clear()
    _state["next_ip"] = 2
    _log("[ue] state reset")


def set_bandwidth(mhz):
    mhz = int(mhz)
    if mhz not in PRB_PER_MHZ:
        raise ValueError(f"Unsupported bandwidth {mhz} MHz, use {sorted(PRB_PER_MHZ)}")
    _state["prb"] = PRB_PER_MHZ[mhz]
    _log(f"[enb] cell bandwidth {mhz} MHz = {_state['prb']} PRB")
    return _state["prb"]


def provision_subscriber(imsi, key, opc):
    _state["subs"][imsi] = {"key": key, "opc": opc}
    _log(f"[hss] subscriber {imsi} provisioned")
    return {"imsi": imsi, "key": key, "opc": opc}


# ---- procedures ------------------------------------------------------------
def _usable():
    return _state["core"] and _state["enb"] and fault() not in ("core_down", "slow")


def attach(imsi, timeout=30.0):
    _log(f"[ue] attach start imsi={imsi} timeout={timeout}s")
    _ev("S1AP", "InitialUEMessage", "0x41", imsi=imsi)
    if not _usable():
        _log("[mme] no response")
        return AttachResult(imsi, "TIMEOUT", setup_ms=int(float(timeout) * 1000))
    if len(_state["bearers"]) >= int(os.environ.get("LAB_MAX_UES", "32")):
        _log("[vm] UE limit reached")
        return AttachResult(imsi, "TIMEOUT", setup_ms=int(float(timeout) * 1000))
    sub = _state["subs"].get(imsi)
    if sub is None:
        _log(f"[mme] Attach Reject imsi={imsi} emm_cause={EMM_UNKNOWN_IMSI}")
        _ev("S1AP", "DownlinkNASTransport", "0x44", imsi=imsi, emm_cause=EMM_UNKNOWN_IMSI)
        return AttachResult(imsi, "REJECTED", EMM_UNKNOWN_IMSI, setup_ms=250)
    if sub["key"] != UE_KEY:
        _log(f"[mme] Authentication Failure imsi={imsi} emm_cause={EMM_MAC_FAILURE}")
        _ev("S1AP", "DownlinkNASTransport", "0x52", imsi=imsi)
        _ev("S1AP", "UplinkNASTransport", "0x5c", imsi=imsi, emm_cause=EMM_MAC_FAILURE)
        _ev("S1AP", "DownlinkNASTransport", "0x54", imsi=imsi)
        return AttachResult(imsi, "REJECTED", EMM_MAC_FAILURE, setup_ms=320)
    if fault() == "flaky" and _state["rng"].random() < 0.15:
        _log(f"[mme] Attach Reject imsi={imsi} emm_cause={EMM_NETWORK_FAILURE}")
        _ev("S1AP", "DownlinkNASTransport", "0x44", imsi=imsi, emm_cause=EMM_NETWORK_FAILURE)
        return AttachResult(imsi, "REJECTED", EMM_NETWORK_FAILURE, setup_ms=400)

    rng = _state["rng"]
    setup_ms = rng.randint(180, 420) + (rng.randint(300, 450) if rng.random() < 0.05 else 0)
    n = _state["n"] = _state["n"] + 1
    ul_teid, dl_teid = 0x1000 + n, 0x2000 + n
    ip = ""
    if fault() != "no_ip":
        ip = "172.16.0.2" if (fault() == "dup_ip" and n >= 2) else f"172.16.0.{_state['next_ip']}"
        _state["next_ip"] += 1
    erab = EBI + 1 if fault() == "erab_mismatch" else EBI
    _state["bearers"][imsi] = {"ip": ip, "ebi": EBI, "ul_teid": ul_teid, "dl_teid": dl_teid}
    _state["idle"].discard(imsi)

    sec = [("DownlinkNASTransport", "0x5d"), ("UplinkNASTransport", "0x5e")]
    auth = [("DownlinkNASTransport", "0x52"), ("UplinkNASTransport", "0x53")]
    for m, c in auth:
        _ev("S1AP", m, c, imsi=imsi)
    if fault() != "bad_order":
        for m, c in sec:
            _ev("S1AP", m, c, imsi=imsi)
    _ev("S1AP", "InitialContextSetupRequest", "0x42", imsi=imsi, erab_id=erab,
        eps_bearer_id=EBI, teid=ul_teid)
    _ev("S1AP", "InitialContextSetupResponse", "", imsi=imsi, erab_id=erab, teid=dl_teid)
    if fault() == "bad_order":
        for m, c in sec:
            _ev("S1AP", m, c, imsi=imsi)
    _ev("S1AP", "UplinkNASTransport", "0x43", imsi=imsi)
    _log(f"[mme] Attach Complete imsi={imsi} ip={ip or 'none'}")
    return AttachResult(imsi, "ATTACHED", ip=ip, setup_ms=setup_ms)


def detach(imsi):
    if imsi in _state["bearers"]:
        _ev("S1AP", "UplinkNASTransport", "0x45", imsi=imsi)
        _ev("S1AP", "DownlinkNASTransport", "0x46", imsi=imsi)
    _state["bearers"].pop(imsi, None)
    _state["idle"].discard(imsi)
    _log(f"[ue] detach imsi={imsi}")


def bearer_exists(imsi):
    return imsi in _state["bearers"]


def get_bearer(imsi):
    return dict(_state["bearers"].get(imsi, {}))


def go_idle(imsi):
    if imsi not in _state["bearers"]:
        raise ValueError(f"{imsi} is not attached")
    _state["idle"].add(imsi)
    _ev("S1AP", "UEContextReleaseCommand", imsi=imsi)
    _log(f"[enb] UE {imsi} released to idle")


def service_request(imsi, downlink_data=True):
    """Idle -> connected. Returns a dict describing what happened."""
    if imsi not in _state["idle"]:
        return {"status": "NOT_IDLE", "paging": False, "bearer_restored": imsi in _state["bearers"]}
    if not _usable():
        return {"status": "TIMEOUT", "paging": downlink_data, "bearer_restored": False}
    if downlink_data:
        _ev("S1AP", "Paging", imsi=imsi)
    b = _state["bearers"][imsi]
    _ev("S1AP", "InitialUEMessage", "", imsi=imsi)
    _ev("S1AP", "InitialContextSetupRequest", "", imsi=imsi, erab_id=EBI,
        eps_bearer_id=EBI, teid=b["ul_teid"])
    _ev("S1AP", "InitialContextSetupResponse", "", imsi=imsi, erab_id=EBI, teid=b["dl_teid"])
    _state["idle"].discard(imsi)
    _log(f"[mme] service request imsi={imsi} paging={downlink_data}")
    return {"status": "ACTIVE", "paging": bool(downlink_data), "bearer_restored": True}


def tau(imsi):
    if imsi not in _state["bearers"]:
        return {"status": "TAU_REJECTED", "cause": 10}
    _ev("S1AP", "InitialUEMessage", "0x48", imsi=imsi)
    _ev("S1AP", "DownlinkNASTransport", "0x49", imsi=imsi)
    _log(f"[mme] TAU accepted imsi={imsi}")
    return {"status": "TAU_ACCEPTED", "cause": None}


# ---- user plane and KPIs ---------------------------------------------------
def ping(imsi, count=10):
    """Return RTT samples in ms and produce GTP-U packets in the capture."""
    b = _state["bearers"].get(imsi)
    if not b or not b["ip"]:
        return []
    rng = _state["rng"]
    extra = 60 if fault() == "high_latency" else 0
    rtts = [round(rng.uniform(18, 34) + extra + (rng.uniform(15, 30) if rng.random() < 0.05 else 0), 1)
            for _ in range(int(count))]
    for _ in range(min(int(count), 2)):
        _ev("GTP-U", "ICMP echo request", imsi=imsi, direction="UL", teid=b["ul_teid"])
        wrong = 0x9999 if fault() == "teid_mismatch" else b["dl_teid"]
        _ev("GTP-U", "ICMP echo reply", imsi=imsi, direction="DL", teid=wrong)
    return rtts


def throughput_samples(direction="DL", duration=10, prb=None, ues=1):
    """Per-second Mbit/s samples. The first two seconds are TCP ramp-up (warm-up)."""
    prb = prb or _state["prb"]
    steady = MBPS_PER_PRB * prb * (0.45 if direction.upper() == "UL" else 1.0)
    steady = steady * 0.97 / max(int(ues), 1)
    if fault() == "low_tput":
        steady *= 0.4
    rng = _state["rng"]
    out = []
    for i in range(int(duration)):
        ramp = (0.3, 0.7)[i] if i < 2 else 1.0
        out.append(round(steady * ramp * rng.uniform(0.97, 1.03), 2))
    _log(f"[iperf3] {direction} {duration}s prb={prb} ues={ues} steady={steady:.1f} Mbit/s")
    return out


# ---- capture ---------------------------------------------------------------
def capture_start():
    _state["events"] = []
    _state["clock"] = 0.0
    _state["capturing"] = True
    _log("[capture] started on S1")


def capture_stop(path):
    _state["capturing"] = False
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump({"note": "simulated capture", "events": _state["events"]}, f, indent=1)
    _log(f"[capture] saved {path}")
    return path


def tail(n=40):
    return "\n".join(_state["log"][-int(n):])


def save_logs(path):
    with open(path, "w") as f:
        f.write("\n".join(_state["log"]) + "\n")
