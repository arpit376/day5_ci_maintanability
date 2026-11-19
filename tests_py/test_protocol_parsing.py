"""Plain Python checks for the NAS order logic (Day 4, slide 'Decode NAS and assert the order').
Run:  python -m unittest discover tests_py -v      (no tshark and no Robot needed)"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "libraries"))
import capture_backend as cb  # noqa: E402

ATT_REQ, AUTH_REQ, SEC_CMD, ATT_ACC = 0x41, 0x52, 0x5D, 0x42


def in_order(seq):
    return seq.index(ATT_REQ) < seq.index(AUTH_REQ) < seq.index(SEC_CMD) < seq.index(ATT_ACC)


class TsharkParsing(unittest.TestCase):
    def test_sample_output_parses(self):
        with open(os.path.join(HERE, "..", "data", "attach_decoded_tshark.txt")) as f:
            seq = cb.parse_tshark_fields(f.read())
        self.assertEqual(seq[0], ATT_REQ)
        self.assertEqual(len(seq), 7)

    def test_blank_lines_and_commas(self):
        self.assertEqual(cb.parse_tshark_fields("0x41\n\n0x52,0x53\n"), [0x41, 0x52, 0x53])

    def test_successful_attach_is_in_order(self):
        with open(os.path.join(HERE, "..", "data", "attach_decoded_tshark.txt")) as f:
            self.assertTrue(in_order(cb.parse_tshark_fields(f.read())))

    def test_wrong_order_is_detected(self):
        self.assertFalse(in_order([0x41, 0x52, 0x42, 0x5D]))

    def test_names(self):
        self.assertEqual(cb.names([0x41, 0x5D]), ["Attach Request", "Security Mode Command"])


if __name__ == "__main__":
    unittest.main()
