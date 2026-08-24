/* bench.c — throughput of the chained pipeline. SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <stdint.h>
#include <time.h>
#include "fluid_detect.h"
int main(void)
{
    uint64_t n = 2684354560ull, acc = 0;
    uint32_t x = 305419896u;
    clock_t t0 = clock();
    for (uint64_t i = 0; i < n; i++) {
        acc += (uint64_t)fd_decide((int32_t)x);
        x = x * 1664525u + 1013904223u;
    }
    double s = (double)(clock() - t0) / CLOCKS_PER_SEC;
    printf("  %llu invocations in %.3f s\n", (unsigned long long)n, s);
    printf("  %.3f ns per chained decision\n", s * 1e9 / (double)n);
    printf("  %.1f million/sec        (sink %llu)\n",
           (double)n / s / 1e6, (unsigned long long)acc);
    return 0;
}
