OSPRAY_VERSION = 1.7.3
OSPRAY = $(abspath ospray-$(OSPRAY_VERSION).x86_64.linux)
CFLAGS = -I$(OSPRAY)/include
LDFLAGS = -L$(OSPRAY)/lib
LDLIBS = -lospray
