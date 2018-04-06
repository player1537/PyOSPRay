CFLAGS = -std=c99
LDFLAGS = -Wl,-rpath /usr/local/lib -lospray

.PHONY: all
all: test

test: test.o
