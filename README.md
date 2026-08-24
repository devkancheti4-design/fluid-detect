# fluid-detect

Two proven kernels in series. One 32-bit word in, one act out.

```
BRAIN 1   detect   1 bit    does the observation differ from what was expected?
BRAIN 2   route    4 bits   which of 16 acts repairs it, inferred from ONE example?
```

```c
#include "fluid_detect.h"

int32_t act = fd_decide(x);   /* 0 = clean, 1..15 = the act to apply */
```

Twelve arm64 instructions for the whole chain. No model, no table, no allocation.

## The register

```
x   0..7    observed signature      what the code actually exhibits
    8..15   expected signature      what it should exhibit
    16..19  worked example: kind    the one fault kind you have labelled
    20..23  worked example: act     the act that repairs that kind
    24..31  ignored — proven never to influence the verdict
```

## The law

```
fd_decide(x) == 0                              when observed == expected
fd_decide(x) == (kind + A1 - F1) mod 16        otherwise,
                where kind = (observed ^ expected) & 15
```

The offset is never stored. It is recovered from the worked example on every
call, so the act vocabulary can be renumbered without touching a line of code —
a lookup table is wrong on 15 of the 16 renumberings; this is wrong on none.

## The guarantee

```
make prove
```

Enumerates **all 4,294,967,296 inputs** against an independently written
reference — written from the law above, not from the expressions.

```
EXHAUSTIVE — all 4,294,967,296 int32 inputs

  chained decide vs reference    : ALL CORRECT  (0)
  bits 24-31 ignored             : ALWAYS      (0)

  THE CLEAN INVARIANT
    observed == expected         : 16777216
      reported non-zero (FALSE ALARM) : NEVER  (0)
    observed != expected         : 4278190080

  8.61 s
  RESULT: PASS
```

**Composition preserves both proofs**, over the complete domain. That is not
automatic: two individually correct kernels can still produce a wrong pipeline
if the intermediate encoding is lossy.

## Provenance

Neither expression was written here. Both are reused verbatim from repositories
where each was authored by a program-synthesis engine and proven exhaustively:

| stage | expression | origin | engine verdict |
|---|---|---|---|
| detect | `fd_weave` / `fd_shield` / `fd_smear` | [weave-kernel](https://github.com/devkancheti4-design/weave-kernel) | proven over 2³² |
| route | `15 & ((y >> 4) + ((y >> 8) - y))` | [fluid-router](https://github.com/devkancheti4-design/fluid-router) | **minimal in D∩I** |

This repository contributes the **join** and its proof — nothing else.

## What the proof caught

The first version of the join was wrong, and the exhaustive sweep found it
immediately. `weave-kernel`'s detector compares **two** lanes (0–7 vs 8–15, and
16–23 vs 24–31). Here only the first lane carries observation-versus-expectation,
so the worked example in bits 16–23 was being compared against the ignored
field:

```
chained decide vs reference : MISMATCH  (15667200)
  reported non-zero (FALSE ALARM) : YES  (15667200)
```

Masking the upper lane before asking fixed it. **A sampled test would have
passed** — the false alarms are 0.36% of the domain and concentrated where a
hand-picked test case is unlikely to look.

## Honest limits

- **The join is not conditional-free, and the kernels are.** Each stage compiles
  without a comparison; the mask that combines them is lowered by clang to
  `tst` + `csel` on arm64. `csel` is branch-free — no misprediction — but it is
  a conditional select, so "no conditional instruction" is true of each brain
  and **not** of the pipeline. Measured, not claimed away:

```
eor w8, w0, w0, lsr #8      ┐
orr w8, w8, w8, lsr #1      │ detect
orr w8, w8, w8, lsr #2      ┘
eor w9, w0, w0, lsl #8      ┐
lsr w10, w0, #20            │
sub w10, w10, w0, lsr #16   │ route
add w9, w10, w9, lsr #8     │
and w9, w9, #0xf            ┘
mov w10, #17                ┐
tst w8, w10                 │ the join   <- the one conditional
csel w0, wzr, w9, eq        ┘
```

- **It routes; it does not repair.** Applying the act, localising the fault and
  verifying the result are all outside this header. On the pipelines measured in
  `fluid-router`, that surrounding work is ~44,000x the cost of the decision.
- **Four bits of fault kind, sixteen acts.** A fault vocabulary wider than that
  needs a different packing.
- **It generalises over translations of the act vocabulary, not permutations.**
  One worked example is consistent with 15! relabellings, exactly one of which
  is a translation. Recovering an arbitrary permutation needs all 16 pairs,
  which is the lookup table itself.
- **`-fwrapv` is required.** The expressions are only the functions they were
  proven to be under wrapping signed arithmetic. The Makefile sets it.
- One machine, one compiler: Apple arm64, clang `-O2`.

## Throughput

```
make bench
```

```
1.825 ns per chained decision      548 million/sec
```

Treat it as throughput, not as a latency guarantee inside your pipeline.

## Commands

```
make prove    all 4,294,967,296 inputs against an independent reference
make bench    throughput of the chain
make asm      the emitted arm64, so you can check the claims above yourself
```

## Licence

MIT. See [LICENSE](LICENSE).
# fluid-detect
