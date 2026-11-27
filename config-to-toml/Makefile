CXXFLAGS ?= -O2 -Wall -Wextra
PYTHON ?= python3

.PHONY: all test clean

all: build/config-to-toml

build/config-to-toml: src/main.cpp
	mkdir -p build
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -std=c++17 $< -o $@

test: all
	$(PYTHON) tests/test_cli.py

clean:
	rm -rf build
