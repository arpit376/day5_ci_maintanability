"""ProtocolLib: capture a procedure and assert on decoded messages (module 4.3)."""
import os

from robot.api import logger
from robot.api.deco import keyword, library
from robot.libraries.BuiltIn import BuiltIn

import capture_backend as cb
import capture_view
import day2_lte as lab


@library(scope="SUITE", auto_keywords=False)
class ProtocolLib:

    @keyword("Start Capture")
    def start_capture(self):
        """Start capturing on the S1 interface."""
        lab.capture_start()

    @keyword("Stop Capture")
    def stop_capture(self, name="capture"):
        """Stop the capture, keep the file in the results folder and return its path."""
        out = BuiltIn().get_variable_value("${OUTPUT DIR}", ".")
        path = lab.capture_stop(os.path.join(out, "captures", f"{name}.capture.json"))
        logger.info(f'<a href="{path}">{name} capture</a>', html=True)
        try:                                   # a Wireshark-style page next to the capture
            view = capture_view.build_html(path)
            logger.info(f'<a href="{os.path.relpath(view, out)}">{name}: open in the capture viewer</a>', html=True)
        except Exception as exc:               # the viewer must never fail a test
            logger.info(f"capture viewer not created: {exc}")
        return path

    @keyword("Get NAS Message Sequence")
    def get_nas_message_sequence(self, capture):
        """Return the EMM message types of the capture, in order, as integers."""
        return cb.nas_sequence(capture)

    @keyword("Get NAS Message Names")
    def get_nas_message_names(self, capture):
        """Return the EMM message names of the capture, in order."""
        return cb.names(cb.nas_sequence(capture))

    @keyword("NAS Messages Should Appear In Order")
    def nas_messages_should_appear_in_order(self, capture, *expected):
        """Check that the named NAS messages occur in this order (others may sit between)."""
        seq = cb.nas_sequence(capture)
        actual = cb.names(seq)
        pos = -1
        for name in expected:
            code = cb.EMM_CODES.get(name.lower())
            if code is None:
                raise ValueError(f"Unknown NAS message name '{name}'")
            if code not in seq[pos + 1:]:
                raise AssertionError(
                    f"'{name}' is missing or out of order. Expected order: {list(expected)}. "
                    f"Captured order: {actual}. Open the capture and check the procedure.")
            pos = seq.index(code, pos + 1)

    @keyword("NAS Message Should Not Appear")
    def nas_message_should_not_appear(self, capture, name):
        """Fail if the named NAS message is in the capture."""
        code = cb.EMM_CODES[name.lower()]
        if code in cb.nas_sequence(capture):
            raise AssertionError(f"'{name}' appears in the capture but must not.")

    @keyword("Get S1AP Message Names")
    def get_s1ap_message_names(self, capture):
        """Return the S1AP message names in order."""
        return [e["msg"] for e in cb.load_events(capture) if e["proto"] == "S1AP"]

    @keyword("S1AP Message Should Not Appear")
    def s1ap_message_should_not_appear(self, capture, name):
        """Fail if the S1AP message is in the capture."""
        if name in self.get_s1ap_message_names(capture):
            raise AssertionError(f"S1AP {name} appears in the capture but must not.")

    @keyword("Reject Cause In Capture Should Be")
    def reject_cause_in_capture_should_be(self, capture, cause):
        """Check the EMM cause carried by the Attach Reject or Authentication Failure."""
        causes = [e.get("emm_cause") for e in cb.load_events(capture) if e.get("emm_cause")]
        if int(cause) not in causes:
            raise AssertionError(f"Expected EMM cause {cause} in the capture, found {causes}.")

    @keyword("E-RAB ID Should Match Bearer ID")
    def erab_id_should_match_bearer_id(self, capture):
        """Initial Context Setup: the E-RAB ID equals the EPS bearer ID in the Attach Accept."""
        ctx = [e for e in cb.load_events(capture) if e["msg"] == "InitialContextSetupRequest"]
        if not ctx:
            raise AssertionError("No Initial Context Setup Request in the capture.")
        for e in ctx:
            if e["erab_id"] != e["eps_bearer_id"]:
                raise AssertionError(
                    f"E-RAB ID {e['erab_id']} does not match EPS bearer ID {e['eps_bearer_id']}.")

    @keyword("Tunnel IDs Should Be Consistent")
    def tunnel_ids_should_be_consistent(self, capture):
        """GTP-U TEIDs equal the TEIDs agreed in Initial Context Setup, both directions."""
        ev = cb.load_events(capture)
        ul = {e["teid"] for e in ev if e["msg"] == "InitialContextSetupRequest"}
        dl = {e["teid"] for e in ev if e["msg"] == "InitialContextSetupResponse"}
        gtp = [e for e in ev if e["proto"] == "GTP-U"]
        if not gtp:
            raise AssertionError("No GTP-U packets in the capture. Send a ping during the capture.")
        for e in gtp:
            expected = ul if e["direction"] == "UL" else dl
            if e["teid"] not in expected:
                raise AssertionError(
                    f"{e['direction']} GTP-U TEID {e['teid']:#x} does not match the setup "
                    f"TEIDs {sorted(hex(t) for t in expected)}.")

    @keyword("GTP-U Should Contain Ping")
    def gtp_u_should_contain_ping(self, capture):
        """A ping (ICMP echo) must be visible inside the GTP-U tunnel."""
        if not any(e["proto"] == "GTP-U" and "echo" in e["msg"] for e in cb.load_events(capture)):
            raise AssertionError("No ICMP echo inside GTP-U. The user plane is not carrying traffic.")
