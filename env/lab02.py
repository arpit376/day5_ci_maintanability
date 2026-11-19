"""Variable file for lab test bed 02. One file per environment (Day 3, slide 12).
Thresholds live here, not in the tests."""
ENB_HOST = "10.0.2.12"
CORE_HOST = "10.0.2.10"
ENB_CONFIG = "enb.conf"

# Test subscriber
IMSI = "001010123456002"
KEY = "00112233445566778899aabbccddeeff"
OPC = "63bfa50ee6523365ff14c1f45f88737d"
WRONG_KEY = "ffffffffffffffffffffffffffffffff"
UNKNOWN_IMSI = "001010999999999"

# Expected EMM causes
EMM_CAUSE_UNKNOWN_IMSI = 8
EMM_CAUSE_MAC_FAILURE = 20

# KPI thresholds
ATTACH_RATE_MIN = 95.0        # percent
SETUP_P95_MAX_MS = 800
DL_MIN_MBPS = 25.0            # 10 MHz cell, one UE
LAT_P95_MAX_MS = 50.0

# Sweep thresholds (Mbit/s per UE)
DL_MIN_5 = 15.0
DL_MIN_10 = 30.0
DL_MIN_20 = 30.0
