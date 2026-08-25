# fluid-detect

**Remember what your code looked like when it worked. Get told the moment it changes.**

You know the bug that isn't a crash. Someone changes `>=` to `>`, or `+ 1` to
`+ 2`, and everything still runs. Tests pass because nobody wrote a test for
that case. It ships. You find out weeks later.

This is a bookmark for your code. You save it when things are good, and it
tells you if anything drifted.

```bash
pip install -e .

fluid-detect record src/     # tests are passing — save this
fluid-detect check  src/     # anything changed since?
```

```
src/mod.py:2: shape moved (act 9)  if x > t:

1 line(s) moved since the baseline.
```

It exits with an error code when something moved, so you can put it in CI or a
git hook and it will stop the commit.

No AI. No internet. No API key. No dependencies at all.

---

## Does it actually work?

I took 4,000 lines of real code from six popular Python packages — code this
tool had never seen — and deliberately broke them, one small change at a time.

**On code I did NOT change, it stayed quiet every single time.**

```
4,000 unchanged lines  →  0 false alarms
```

That matters more than anything else. A tool that cries wolf gets turned off in
a week.

**On code I did change, it noticed 438 out of 443 times.**

| the kind of change | how many I made | how many it caught |
|---|---|---|
| `>=` became `>` | 17 | 15 |
| a number changed by one | 375 | **all 375** |
| `+` became `-` | 45 | 42 |
| `*` became `/` | 6 | **all 6** |

Run it yourself: `python3 tests/test_guard.py`

## What an outside reviewer found, and what it cost me

Someone read the first version and said, in effect: *this records whether a line
has a comparison or an arithmetic operator, warns if that changes, and breaks
the moment you insert a line — nothing `git diff` cannot do better.*

**They were right on every count, and one of the causes was worse than they
knew.** Both problems are fixed; both are recorded here rather than quietly
corrected.

**1. Inserting a line broke it.** Lines were compared by position, so adding one
comment at the top reported every following line as changed — measured at **5
false alarms from a single inserted comment.** Lines are now *aligned* with
`difflib` before comparison, so insertions, deletions and reorderings shift
nothing. `tests/test_line_shift.py` is the regression test.

**2. The deeper cause: the layout threw away what the kernel routes on.** The
deciding kernel routes on the low four bits of the difference. The first layout
put arithmetic operators in the *high* four bits — the detector saw them, the
router never did. Every arithmetic change collapsed to one indistinguishable
answer, and `*` vs `/` was invisible entirely (0 of 6 caught).

The variant now lives in the low nibble, so each kind of change gets its own
answer:

```
change              answer
no change                0
comparison changed       5
+ became -               6
* became /               8
a literal changed       12
```

That is the difference between *"something moved"* — which `git diff` genuinely
does better — and *"something moved, and here is which kind of change it was"*,
which is the part a repair tool can act on.

## Why you can trust the part that does the deciding

Underneath is a tiny piece of arithmetic — twelve machine instructions — that
makes the actual "did this change?" decision.

Most software is tested by trying some examples and hoping they were the right
ones. This one was checked against **every possible input it can ever receive.**
All 4,294,967,296 of them. Not a sample. The whole thing, in about eight
seconds:

```
make prove
```

That check earned its keep immediately. My first attempt at wiring the pieces
together was **wrong on 15,667,200 inputs** — about a third of one percent.
Any normal test suite would have passed it. The exhaustive check found it on
the first run.

There's also a test that confirms the Python version and the C version agree
(`0 of 200,000 disagree`), because if they ever drift apart, the Python package
would be quietly claiming a guarantee it no longer has.

---

## Its sibling: the one that fixes things

[**fluid-router**](https://github.com/devkancheti4-design/fluid-router) is the
repair half. Same idea, opposite job.

|  | what it does |
|---|---|
| **fluid-detect** (this) | *notices* that something changed |
| **fluid-router** | *repairs* it |

They need different things to work, and that difference matters:

- **The repairer has to guess what the code was supposed to be.** That's the
  hard part of debugging.
- **This one doesn't have to guess.** "Supposed to be" is just whatever you
  saved when the tests were passing.

I tested that difference rather than assuming it. Using this detector to *find*
unknown bugs — where it had to guess what was expected — it hid three real bugs
out of five. Using it to *notice changes* from a saved snapshot, it caught 98%
with no false alarms. Same code, right job versus wrong job.

---

## Commands

```
fluid-detect record PATHS      save the current shape
fluid-detect check  PATHS      exit 1 if anything moved

make prove                     check the kernel against all 4.29 billion inputs
make bench                     how fast it is (1.8 nanoseconds per check)
python3 tests/test_guard.py    reproduce the results table above
python3 tests/test_kernel_parity.py   confirm Python matches C
```

## Where it came from

The deciding arithmetic wasn't written by hand. It was **generated by a
program-synthesis engine** from input/output examples, and it appears here
exactly as the engine produced it — no tidying up. Two pieces are borrowed from
sibling projects, [weave-kernel](https://github.com/devkancheti4-design/weave-kernel)
and [fluid-router](https://github.com/devkancheti4-design/fluid-router), each
already checked against its own complete set of inputs. What this project adds
is the way they're joined together, and the proof that joining them didn't
break either one.

## Licence

MIT — use it for anything, including commercially.
