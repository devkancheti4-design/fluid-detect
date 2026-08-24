CC     ?= cc
CFLAGS ?= -O2 -std=c11 -fwrapv -Wall -Wextra -Iinclude

.PHONY: all prove bench asm clean
all: prove

build:
	@mkdir -p build

prove: build
	$(CC) $(CFLAGS) -o build/prove test/prove.c
	./build/prove

bench: build
	$(CC) $(CFLAGS) -o build/bench test/bench.c
	./build/bench

asm:
	@printf '#include "fluid_detect.h"\nint32_t f(int32_t x){return fd_decide(x);}\n' \
	  | $(CC) $(CFLAGS) -S -o - -x c - | sed -n '/^_\?f:/,/ret/p'

clean:
	rm -rf build
