CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra
TARGET = build/depviz
SOURCE = src/main.cpp

.PHONY: all test clean

all: $(TARGET)

$(TARGET): $(SOURCE)
	mkdir -p build
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCE)

test: $(TARGET)
	sh tests/test_graph.sh

clean:
	rm -rf build
