"""Read a capture and return decoded messages.

* ``*.json``       simulated capture written by day2_lte.capture_stop (default in this kit)
* ``*.pcap/.pcapng`` a real capture: decoded with tshark (needs tshark installed)

The real-pcap path implements the NAS message order (slide 22). Extending
``tshark_events`` to S1AP IEs and GTP-U TEIDs is the stretch exercise on the lab VM.
"""
import json
import subprocess

EMM_NAMES = {
    0x41: "Attach Request", 0x42: "Attach Accept", 0x43: "Attach Complete",
    0x44: "Attach Reject", 0x45: "Detach Request", 0x46: "Detach Accept",
    0x48: "TAU Request", 0x49: "TAU Accept", 0x52: "Authentication Request",
    0x53: "Authentication Response", 0x54: "Authentication Reject",
    0x5c: "Authentication Failure", 0x5d: "Security Mode Command",
    0x5e: "Security Mode Complete",
}
EMM_CODES = {name.lower(): code for code, name in EMM_NAMES.items()}


def parse_tshark_fields(text):
    """tshark -T fields output -> list of EMM message type codes (ints).
    Handles blank lines, several values per frame (comma separated) and 0x prefixes."""
    seq = []
    for token in text.replace(",", " ").split():
        seq.append(int(token, 16))
    return seq


def tshark_nas_sequence(pcap):
    out = subprocess.check_output(
        ["tshark", "-r", pcap, "-Y", "nas-eps", "-T", "fields",
         "-e", "nas_eps.nas_msg_emm_type"], text=True)
    return parse_tshark_fields(out)


def load_events(path):
    if not path.endswith(".json"):
        raise NotImplementedError(
            "S1AP and GTP-U checks on a real pcap are the stretch exercise: extend "
            "tshark_events() in capture_backend.py (use -e s1ap.* and -e gtp.teid).")
    with open(path) as f:
        return json.load(f)["events"]


def nas_sequence(path):
    if path.endswith(".json"):
        return [int(e["nas_type"], 16) for e in load_events(path) if e.get("nas_type")]
    return tshark_nas_sequence(path)


def names(sequence):
    return [EMM_NAMES.get(c, hex(c)) for c in sequence]
