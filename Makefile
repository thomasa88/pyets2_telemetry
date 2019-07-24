#
# Copyright 2019 Thomas Axelsson <thomasa88@gmail.com>
#
# This file is part of pyets2_telemetry.
#
# pyets2_telemetry is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyets2_telemetry is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyets2_telemetry.  If not, see <https://www.gnu.org/licenses/>.
#

SDK_DIR ?= eurotrucks2_telemetry_sdk_1.10

SDK_CFLAGS := -I$(SDK_DIR)/include

PYTHON_CFLAGS := $(shell pkg-config --cflags python3)
PYTHON_LDFLAGS := $(shell pkg-config --libs python3)

CXXFLAGS := $(SDK_CFLAGS) $(PYTHON_CFLAGS) -std=c++17 -fPIC -Wall -O2
LDFLAGS := $(PYTHON_LDFLAGS)

VERSION := $(shell cut -d '"' -f 2 version.hpp | sed 's/\./_/g')
INCS := pyhelp.hpp log.hpp version.hpp
SRCS := loader.cpp pyhelp.cpp log.cpp
LIBRARY_BASENAME := pyets2_telemetry_loader
LIBRARY := $(LIBRARY_BASENAME).so
VERSIONED_LIBRARY := $(LIBRARY_BASENAME)_$(VERSION).so
DEV_LIBRARY := $(LIBRARY_BASENAME)_dev.so
PY_PLUGIN_DIR := python
PY_PKG_DIR := $(PY_PLUGIN_DIR)/pyets2lib
PY_FILES := $(wildcard $(PY_PKG_DIR)/*.py)
TAR_NAME := pyets2_telemetry_$(VERSION).tar.bz2

TEST_SRCS := $(SRCS) test.cpp

.DEFAULT_GOAL: $(LIBRARY)

$(LIBRARY): $(SRCS) $(INCS)
	g++ $(CXXFLAGS) -o $@ --shared -Wl,--no-allow-shlib-undefined -Wl,-soname,$@  $(SRCS) $(LDFLAGS)

test: $(TEST_SRCS)
	g++ $(CXXFLAGS) -g -o $@ $(TEST_SRCS) $(LDFLAGS)

.PHONY: install
install: uninstall $(LIBRARY) $(PY_FILES)
	@( [ "x$(DESTDIR)" != "x" ] && [ -e "$(DESTDIR)" ] ) || \
	  ( echo 'Please provide DESTDIR="<ETS2 PLUGIN DIR>"'; exit 1; )
	@install $(LIBRARY) "$(DESTDIR)/$(VERSIONED_LIBRARY)"
	@install -D $(PY_FILES) -t "$(DESTDIR)/$(PY_PKG_DIR)"
	@echo "Installed in \"$(DESTDIR)\""

# Set up symbolic links to the repository
.PHONY: install-dev
install-dev: uninstall
	@( [ "x$(DESTDIR)" != "x" ] && [ -e "$(DESTDIR)" ] ) || \
	  ( echo 'Please provide DESTDIR="<ETS2 PLUGIN DIR>"'; exit 1; )
	@cp -fs $(PWD)/$(LIBRARY) "$(DESTDIR)/$(DEV_LIBRARY)"
	@mkdir -p "$(DESTDIR)/$(PY_PLUGIN_DIR)"
	@ln -s $(PWD)/$(PY_PKG_DIR) "$(DESTDIR)/$(PY_PKG_DIR)"
	@echo "Installed links in \"$(DESTDIR)\""

.PHONY: uninstall
uninstall:
	@( [ "x$(DESTDIR)" != "x" ] && [ -e "$(DESTDIR)" ] ) || \
	  ( echo 'Please provide DESTDIR="<ETS2 PLUGIN DIR>"'; exit 1; )
	@rm -f -- "$(DESTDIR)/$(LIBRARY_BASENAME)"*
	@rm -rf "$(DESTDIR)/$(PY_PKG_DIR)"
# Remove python dir if it is empty
	@[ ! -e "$(DESTDIR)/$(PY_PLUGIN_DIR)" ] || rmdir --ignore-fail-on-non-empty "$(DESTDIR)/$(PY_PLUGIN_DIR)"
	@echo "Uninstalled from \"$(DESTDIR)\""

.PHONY: package
package: $(LIBRARY) $(PY_FILES)
	@tar --transform='flags=r;s|$(LIBRARY)|$(VERSIONED_LIBRARY)|' \
	  -cjf $(TAR_NAME) $^
	@echo "Created $(TAR_NAME)"
