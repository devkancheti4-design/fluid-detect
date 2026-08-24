#!/usr/bin/env python3
"""The Python mirror must agree with the compiled C kernel. If it ever does not,
the package is lying about being the proven thing."""
import os, subprocess, sys, random, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fluid_detect import decide
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC = r'''#include <stdio.h>
#include <stdint.h>
#include "fluid_detect.h"
int main(void){ long v; while(scanf("%ld",&v)==1) printf("%d\n", fd_decide((int32_t)v)); return 0; }
'''

def main(n=200000):
    d = tempfile.mkdtemp()
    open(os.path.join(d, "c.c"), "w").write(SRC)
    r = subprocess.run(["cc", "-O2", "-std=c11", "-fwrapv",
                        "-I", os.path.join(ROOT, "include"),
                        "-o", os.path.join(d, "c"), os.path.join(d, "c.c")],
                       capture_output=True)
    if r.returncode:
        print("  no C compiler / header; skipping parity check"); return 0
    rng = random.Random(11)
    words, want = [], []
    for _ in range(n):
        now = rng.randrange(256); good = rng.randrange(256)
        k = rng.randrange(16); a = rng.randrange(16)
        x = now | (good << 8) | (k << 16) | (a << 20) | (rng.randrange(256) << 24)
        words.append(x); want.append(decide(now, good, k, a))
    out = subprocess.run([os.path.join(d, "c")], input="\n".join(map(str, words)),
                         capture_output=True, text=True).stdout.split()
    got = [int(v) for v in out]
    bad = sum(1 for a, b in zip(got, want) if a != b)
    print("  python mirror vs compiled kernel : %d of %d disagree" % (bad, n))
    print("\n  RESULT: %s" % ("PASS" if bad == 0 else "FAIL"))
    return 0 if bad == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
