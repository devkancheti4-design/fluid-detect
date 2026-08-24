/* fluid_detect.h — two proven kernels in series: detect, then route.
 *
 * SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Devieswar Kancheti
 *
 * BRAIN 1  fd_detect  1 bit   does the observation differ from what was expected?
 * BRAIN 2  fd_route   4 bits  which of 16 acts repairs it, inferred from ONE example?
 *
 * Both expressions are reused verbatim from their origin repositories, where each
 * was authored by a program-synthesis engine and proven over its complete domain:
 *   fd_weave / fd_shield / fd_smear   <- weave-kernel   (columnar bit-weaving)
 *   fd_route                          <- fluid-router   (minimal in D∩I)
 * Neither was hand-written or hand-simplified here. This header adds only the join.
 *
 * THE REGISTER
 *   x  0..7    observed signature      what the code actually exhibits
 *      8..15   expected signature      what it should exhibit
 *      16..19  worked example: kind    the one fault kind you have labelled
 *      20..23  worked example: act     the act that repairs that kind
 *      24..31  ignored
 *
 * THE LAW
 *   fd_decide(x) == 0                                    when observed == expected
 *   fd_decide(x) == (kind_q + A1 - F1) mod 16            otherwise,
 *                   where kind_q = (observed ^ expected) & 15
 *
 * Build with -fwrapv. The expressions are only the functions they were proven to
 * be under wrapping signed arithmetic.
 */
#ifndef FLUID_DETECT_H
#define FLUID_DETECT_H
#include <stdint.h>

/* ---- BRAIN 1: detection (weave-kernel, verbatim) ------------------------- */
static inline uint32_t fd_weave (uint32_t x){ return ((x & 16711935u) ^ (16711935u & (x >> 8))); }
static inline uint32_t fd_shield(uint32_t x){ return (255u & (x | (x >> 16))); }
static inline uint32_t fd_smear (uint32_t x){
    uint32_t a = x | (x >> 1);
    uint32_t b = a | (a >> 2);
    return 1u & (b | (b >> 4));
}
/* 1 iff the low two lanes of x disagree */
static inline uint32_t fd_detect(uint32_t x){ return fd_smear(fd_shield(fd_weave(x))); }

/* ---- BRAIN 2: routing (fluid-router, verbatim, minimal in D∩I) ----------- */
/* y packs F1 | (A1<<4) | (Fq<<8);  returns (Fq + A1 - F1) mod 16 */
static inline int32_t fd_route(int32_t y){ return 15 & ((y >> 4) + ((y >> 8) - y)); }

/* ---- THE JOIN ------------------------------------------------------------ */
/* Arithmetic, not conditional: the router's output is masked by the detector's
 * bit. Note that clang still lowers this to tst+csel on arm64 -- csel is
 * branch-free but it is a conditional select, so the "no conditional
 * instruction" property of each kernel does NOT survive the join verbatim.
 * Measured and stated rather than claimed away; see README. */
static inline int32_t fd_decide(int32_t x)
{
    uint32_t ux  = (uint32_t)x;
    /* weave-kernel's detector compares TWO lanes (0-7 vs 8-15, and 16-23 vs
     * 24-31). Here only the first lane carries observation-vs-expectation, so
     * the upper lane is zeroed before it is asked -- otherwise the worked
     * example in bits 16-23 is compared against the ignored field and the
     * detector fires spuriously. The exhaustive proof caught exactly that:
     * 15,667,200 false alarms before this mask was added. */
    uint32_t d   = fd_detect(ux & 0xFFFFu);       /* 0 or 1 */
    int32_t kind = (int32_t)(((ux ^ (ux >> 8)) & 15u));
    int32_t F1   = (int32_t)((ux >> 16) & 15u);
    int32_t A1   = (int32_t)((ux >> 20) & 15u);
    int32_t y    = F1 | (A1 << 4) | (kind << 8);
    return fd_route(y) & (int32_t)(0u - d);
}

#endif /* FLUID_DETECT_H */
