#!/usr/bin/env python3
"""The measurement, reproducible: recall on mutations, false alarms on unchanged
code. Runs against whatever site-packages you have -- no fixtures committed."""
import glob, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fluid_detect import signature, decide

MUT = [
    ("cmp_strictness", lambda l: l.replace(">=", ">", 1) if ">=" in l
                       else (l.replace("<=", "<", 1) if "<=" in l else None)),
    ("off_by_one",     lambda l: re.sub(r"\b(\d+)\b",
                       lambda m: str(int(m.group(1)) + 1), l, count=1)
                       if re.search(r"\b\d+\b", l) else None),
    ("additive_flip",  lambda l: l.replace(" + ", " - ", 1) if " + " in l
                       else (l.replace(" - ", " + ", 1) if " - " in l else None)),
    ("mul_div_flip",   lambda l: l.replace(" * ", " / ", 1) if " * " in l else None),
]

def corpus(limit=4000):
    sp = [p for p in sys.path if p.endswith("site-packages")]
    if not sp:
        return []
    lines = []
    for d in sorted(glob.glob(os.path.join(sp[0], "*")))[:40]:
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "*.py")))[:8]:
            try:
                for l in open(f, encoding="utf-8", errors="ignore").read().splitlines():
                    if 12 < len(l.strip()) < 100 and not l.strip().startswith("#"):
                        lines.append(l)
            except OSError:
                pass
    random.Random(5).shuffle(lines)
    return lines[:limit]

def main():
    lines = corpus()
    if not lines:
        print("no corpus available (need site-packages); skipping"); return 0
    fa = sum(1 for l in lines if decide(signature(l), signature(l)) != 0)
    caught = {k: [0, 0] for k, _ in MUT}
    for l in lines:
        for name, fn in MUT:
            m = fn(l)
            if m is None or m == l:
                continue
            caught[name][1] += 1
            if decide(signature(m), signature(l)) != 0:
                caught[name][0] += 1
    print("  corpus lines                 : %d" % len(lines))
    print("  unchanged code, false alarms : %d  (%.2f%%)\n" % (fa, 100.0 * fa / len(lines)))
    print("  %-16s %8s %8s %8s" % ("mutation", "planted", "caught", "recall"))
    print("  " + "-" * 46)
    tc = tp = 0
    for k, (c, t) in caught.items():
        tc += c; tp += t
        print("  %-16s %8d %8d %7.1f%%" % (k, t, c, 100.0 * c / t if t else 0))
    print("  " + "-" * 46)
    print("  %-16s %8d %8d %7.1f%%" % ("TOTAL", tp, tc, 100.0 * tc / tp if tp else 0))
    ok = (fa == 0)
    print("\n  RESULT: %s   (gate: zero false alarms on unchanged code)"
          % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
