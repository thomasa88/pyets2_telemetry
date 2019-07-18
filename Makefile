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

# Check flags and manually take the ones we want
#PYTHON_CFLAGS := $(shell python3.6-config --cflags)
PYTHON_CFLAGS := $(shell pkg-config --cflags python3)

# Remove? Check flags and manually take the ones we want
#PYTHON_LDFLAGS := $(shell python3.6-config --ldflags)
PYTHON_LDFLAGS := $(shell pkg-config --libs python3)
#-L/usr/lib/python3.6/config-3.6m-x86_64-linux-gnu

# -O2
CXXFLAGS := $(PYTHON_CFLAGS) -std=c++17 -fPIC -Wall
LDFLAGS := $(PYTHON_LDFLAGS) 

SRCS := loader.cpp

TEST_SRCS := $(SRCS) test.cpp

pyets2_telemetry_loader.so: $(SRCS) $(SDK_HEADERS)
	g++ $(CXXFLAGS) -o $@ --shared -Wl,--no-allow-shlib-undefined -Wl,$(LIB_NAME_OPTION),$@ $(SDK_INCLUDES) $(SRCS) $(PYTHON_LDFLAGS)

test: $(TEST_SRCS) $(SDK_HEADERS)
	g++ $(CXXFLAGS) -g -o $@ $(SDK_INCLUDES) $(TEST_SRCS) $(LDFLAGS)
