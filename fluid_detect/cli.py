"""fluid-detect — record a baseline while the tests are green, then check."""
from __future__ import annotations
import argparse, json, os, sys
from . import Guard, __version__

DEFAULT = ".fluid-detect.json"

def _walk(paths):
    for p in paths:
        if os.path.isfile(p) and p.endswith(".py"):
            yield p
        for root, _, files in os.walk(p):
            if any(part.startswith((".", "__pycache__")) for part in root.split(os.sep)):
                continue
            for f in files:
                if f.endswith(".py"):
                    yield os.path.join(root, f)

def main(argv=None):
    ap = argparse.ArgumentParser(prog="fluid-detect",
        description="Record what your code looked like when it was right; "
                    "be told the moment its shape moves.")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", help="tests are green: remember this shape")
    r.add_argument("paths", nargs="+")
    r.add_argument("-o", "--out", default=DEFAULT)
    c = sub.add_parser("check", help="has anything moved since?")
    c.add_argument("paths", nargs="+")
    c.add_argument("-b", "--baseline", default=DEFAULT)
    ns = ap.parse_args(argv)

    if ns.cmd == "record":
        g = Guard()
        n = 0
        for f in _walk(ns.paths):
            g.record(f, open(f, encoding="utf-8", errors="ignore").read()); n += 1
        json.dump(g.to_dict(), open(ns.out, "w"), indent=1)
        print("recorded %d files -> %s" % (n, ns.out))
        return 0

    if not os.path.exists(ns.baseline):
        print("no baseline at %s -- run `fluid-detect record` first" % ns.baseline,
              file=sys.stderr)
        return 2
    g = Guard.from_dict(json.load(open(ns.baseline)))
    moved = 0
    for f in _walk(ns.paths):
        for lineno, act, line in g.check(f, open(f, encoding="utf-8",
                                                 errors="ignore").read()):
            moved += 1
            print("%s:%d: shape moved (act %d)  %s" % (f, lineno, act, line.strip()[:70]))
    if moved:
        print("\n%d line(s) moved since the baseline." % moved)
        return 1
    print("clean — every recorded line still has the shape it had.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
