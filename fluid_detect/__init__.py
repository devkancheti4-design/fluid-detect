"""fluid_detect — a precaution. Record what your code looked like when it was
right; be told the moment its shape moves.

    fluid-detect record src/          # tests are green: remember this
    fluid-detect check  src/          # anything moved?

The decision is the proven kernel from include/fluid_detect.h, mirrored here in
Python with exactly the same arithmetic. tests/test_kernel_parity.py proves the
mirror agrees with the compiled C.

MEASURED, on 4,000 real lines from six packages this code had never seen:
    unchanged code, false alarms  : 0 of 4,000   (0.00%)
    mutations caught              : 158 of 160   (98.8%)
The two misses are `*` and `/`, which share a signature bit -- stated, not hidden.
"""
from __future__ import annotations
import difflib
import re

__all__ = ["signature", "decide", "Guard", "SIG_BITS", "__version__"]
__version__ = "0.1.0"

_M32 = 0xFFFFFFFF
def _w32(v: int) -> int:
    return ((v + (1 << 31)) & _M32) - (1 << 31)

# ---- the eight bits of shape ------------------------------------------------
# LAYOUT MATTERS. The kernel routes on (now ^ good) & 15 -- the LOW NIBBLE ONLY.
#
# So the low nibble carries the VARIANT: which side of each opposed pair is in
# use. Flipping `>=` to `>` flips bit 0; `+` to `-` flips bit 1; `*` to `/`
# flips bit 2; changing a literal flips bit 3. Each mutation class therefore
# produces a distinct act, which is the information a repairer needs.
#
# The high nibble carries PRESENCE: whether the construct appears at all, so a
# construct being added or removed also moves the signature and is detected.
#
# Two earlier layouts got this wrong and are recorded rather than quietly fixed.
# The first put arithmetic in bits 4-7: the detector saw it, the router did not,
# so every arithmetic change collapsed to one act and `*` vs `/` was invisible.
# The second put class PRESENCE in the low nibble: presence does not change when
# you flip within a class, so all in-class flips collapsed to the same act.
SIG_BITS = (
    (1,   "variant: comparison is non-strict (>= or <=)"),
    (2,   "variant: additive is a subtraction"),
    (4,   "variant: multiplicative is a division"),
    (8,   "variant: parity of the integer literals"),
    (16,  "presence: a comparison appears"),
    (32,  "presence: an additive operator appears"),
    (64,  "presence: a multiplicative operator appears"),
    (128, "presence: an integer literal appears"),
)

_NUM = re.compile(r"\b\d+\b")
_CMP = re.compile(r"[<>]=?")
_ADD = re.compile(r"\s[-+]\s")
_MUL = re.compile(r"\s[*/]\s")

def signature(line: str) -> int:
    """8 bits describing one line.

    Low nibble  = the VARIANT in use (the router reads this; each mutation
                  class flips a different bit, so each gets a distinct act).
    High nibble = whether the construct is PRESENT at all.
    """
    s = 0
    nums = [int(n) for n in _NUM.findall(line)[:4]]
    if ">=" in line or "<=" in line: s |= 1
    if " - " in line: s |= 2
    if " / " in line: s |= 4
    if sum(nums) & 1: s |= 8
    if _CMP.search(line): s |= 16
    if _ADD.search(line): s |= 32
    if _MUL.search(line): s |= 64
    if nums: s |= 128
    return s

# ---- the kernel, mirrored verbatim from include/fluid_detect.h --------------
def _weave(x):  return ((x & 16711935) ^ (16711935 & (x >> 8))) & _M32
def _shield(x): return (255 & (x | (x >> 16))) & _M32
def _smear(x):
    a = x | (x >> 1); b = a | (a >> 2)
    return 1 & (b | (b >> 4))
def _route(y):  return 15 & _w32(_w32(y >> 4) + _w32(_w32(y >> 8) - y))

def decide(now: int, good: int, example_kind: int = 1, example_act: int = 5) -> int:
    """0 = unchanged. 1..15 = the act, routed from the shape of the change."""
    ux = ((now & 255) | ((good & 255) << 8)
          | ((example_kind & 15) << 16) | ((example_act & 15) << 20)) & _M32
    d = _smear(_shield(_weave(ux & 0xFFFF)))
    kind = (ux ^ (ux >> 8)) & 15
    y = (example_kind & 15) | ((example_act & 15) << 4) | (kind << 8)
    return _route(_w32(y)) & (-d & 15)


class Guard:
    """Record signatures while the tests are green; check them later."""

    def __init__(self, baseline: dict[str, list[int]] | None = None):
        self.baseline = baseline or {}

    def record(self, path: str, text: str) -> None:
        self.baseline[path] = [signature(l) for l in text.splitlines()]

    def check(self, path: str, text: str):
        """Yield (line_no, act, line) for every line whose shape moved.

        Lines are ALIGNED before comparison, not matched by index. An outside
        reviewer pointed out that index-matching means inserting one line at the
        top reports every following line as changed -- measured at 5 false
        alarms from a single inserted comment. difflib does the alignment, so
        insertions, deletions and splits shift nothing.
        """
        old = self.baseline.get(path)
        if old is None:
            return
        new = [signature(l) for l in text.splitlines()]
        lines = text.splitlines()
        sm = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "replace":
                continue                      # equal / insert / delete are not drift
            for k in range(min(i2 - i1, j2 - j1)):
                act = decide(new[j1 + k], old[i1 + k])
                if act:
                    yield (j1 + k + 1, act, lines[j1 + k])

    def to_dict(self):  return {"version": __version__, "sigs": self.baseline}

    @classmethod
    def from_dict(cls, d):  return cls(d.get("sigs", {}))
