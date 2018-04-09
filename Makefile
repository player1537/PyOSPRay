CFLAGS = -std=c99
LDFLAGS = -Wl,-rpath /usr/local/lib -lospray

.PHONY: all
all:

.PHONY: run
run: .mk.depend
	./venv/bin/python test.py

.PHONY: depend
depend: .mk.depend

.mk.depend: setup.py ospray.py ospray_wrap.c
	python3.6 -m virtualenv venv
	./venv/bin/pip install -e .
	touch $@

ospray.py: .mk.swig
	touch $@

ospray_wrap.c: .mk.swig
	touch $@

.mk.swig: ospray.i
	swig -python -I/usr/local/include/ospray ospray.i
	touch $@

