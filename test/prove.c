/* prove.c — the entire 32-bit input domain, against an independently written
 * reference. Not a sample. SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <stdint.h>
#include <time.h>
#include "fluid_detect.h"

/* Independent reference. Deliberately written from the LAW in the header's
 * comment, not from the expressions. */
static int32_t ref_decide(uint32_t x)
{
    uint32_t obs = x & 255u;
    uint32_t exp = (x >> 8) & 255u;
    if (obs == exp) return 0;
    int32_t kind = (int32_t)((obs ^ exp) & 15u);
    int32_t F1   = (int32_t)((x >> 16) & 15u);
    int32_t A1   = (int32_t)((x >> 20) & 15u);
    int32_t m    = (kind + A1 - F1) % 16;
    return (m < 0) ? m + 16 : m;
}

int main(void)
{
    uint64_t bad = 0, clean = 0, faulty = 0, leak = 0, pollution = 0;
    clock_t t0 = clock();
    uint32_t u = 0;
    do {
        int32_t got = fd_decide((int32_t)u);
        int32_t want = ref_decide(u);
        if (got != want) bad++;
        if (((u & 255u) == ((u >> 8) & 255u))) { clean++; if (got != 0) leak++; }
        else faulty++;
        /* bits 24-31 must never influence the verdict */
        if (fd_decide((int32_t)u) != fd_decide((int32_t)(u & 0x00FFFFFFu))) pollution++;
        u++;
    } while (u != 0);
    double s = (double)(clock() - t0) / CLOCKS_PER_SEC;

    printf("EXHAUSTIVE — all 4,294,967,296 int32 inputs\n\n");
    printf("  chained decide vs reference    : %s  (%llu)\n",
           bad ? "MISMATCH" : "ALL CORRECT", (unsigned long long)bad);
    printf("  bits 24-31 ignored             : %s  (%llu)\n",
           pollution ? "NO" : "ALWAYS   ", (unsigned long long)pollution);
    printf("\n  THE CLEAN INVARIANT\n");
    printf("    observed == expected         : %llu\n", (unsigned long long)clean);
    printf("      reported non-zero (FALSE ALARM) : %s  (%llu)\n",
           leak ? "YES" : "NEVER", (unsigned long long)leak);
    printf("    observed != expected         : %llu\n", (unsigned long long)faulty);
    printf("\n  %.2f s\n", s);
    printf("\n  RESULT: %s\n", (bad || leak || pollution) ? "FAIL" : "PASS");
    return (bad || leak || pollution) ? 1 : 0;
}
