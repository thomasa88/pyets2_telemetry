SDK_DIR=$(HOME)/src/eurotrucks2_telemetry_sdk_1.10

SDK_HEADERS=\
        $(SDK_DIR)/include/*.h \
        $(SDK_DIR)/include/common/*.h \
        $(SDK_DIR)/include/amtrucks/*.h \
        $(SDK_DIR)/include/eurotrucks2/*.h

SDK_INCLUDES=\
        -I$(SDK_DIR)/include \
        -I$(SDK_DIR)/include/common/ \
        -I$(SDK_DIR)/include/amtrucks/ \
        -I$(SDK_DIR)/include/eurotrucks2

UNAME:= $(shell uname -s)

ifeq ($(UNAME),Darwin)
LIB_NAME_OPTION=-install_name
else
LIB_NAME_OPTION=-soname
endif

PYTHON_CFLAGS := $(shell pkg-config --cflags python3)
PYTHON_LDFLAGS := $(shell pkg-config --libs python3)

CXXFLAGS := $(PYTHON_CFLAGS) -std=c++17 -fPIC -Wall -O2
LDFLAGS := $(PYTHON_LDFLAGS)

VERSION := $(shell cut -d ' ' -f 3 version.hpp | sed 's/\./_/g')
INCS := pyhelp.hpp log.hpp version.hpp
SRCS := loader.cpp pyhelp.cpp log.cpp
LIBRARY := pyets2_telemetry_loader.so

TEST_SRCS := $(SRCS) test.cpp

.DEFAULT_GOAL: $(LIBRARY)

$(LIBRARY): $(SRCS) $(INCS) $(SDK_HEADERS)
	g++ $(CXXFLAGS) -o $@ --shared -Wl,--no-allow-shlib-undefined -Wl,$(LIB_NAME_OPTION),$@ $(SDK_INCLUDES) $(SRCS) $(LDFLAGS)

test: $(TEST_SRCS) $(SDK_HEADERS)
	g++ $(CXXFLAGS) -g -o $@ $(SDK_INCLUDES) $(TEST_SRCS) $(LDFLAGS)
