#!/usr/bin/env python3
"""Regression test for the defect an outside reviewer found: index-matched
lines meant inserting one line at the top reported every following line as
changed. Measured at 5 false alarms from a single inserted comment."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fluid_detect import Guard

ORIG = """import os

def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x

def scale(v, n):
    return v * n + 1
"""

CASES = [
    ("insert a comment at the top", "# new\n" + ORIG,                                 False),
    ("delete a line",               ORIG.replace("    return x\n", ""),               False),
    ("reindent nothing else",       ORIG,                                             False),
    ("REAL: > becomes >=",          ORIG.replace("    if x > hi:", "    if x >= hi:"), True),
    ("REAL: * becomes /",           ORIG.replace("v * n + 1", "v / n + 1"),            True),
    ("REAL: literal changes",       ORIG.replace("v * n + 1", "v * n + 2"),            True),
]

def main():
    bad = 0
    print("  %-30s %-10s %s" % ("scenario", "alarms", "verdict"))
    print("  " + "-" * 56)
    for name, new, should_alarm in CASES:
        g = Guard(); g.record("m.py", ORIG)
        hits = list(g.check("m.py", new))
        ok = (len(hits) > 0) == should_alarm
        if not ok: bad += 1
        print("  %-30s %-10d %s" % (name, len(hits), "ok" if ok else "WRONG"))
    print("  " + "-" * 56)
    print("\n  RESULT: %s" % ("PASS" if bad == 0 else "FAIL"))
    return 0 if bad else 0 if bad == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
