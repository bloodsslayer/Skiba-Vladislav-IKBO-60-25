#!/bin/sh
# Сборка эмулятора (нужен FLTK: brew install fltk)
c++ -std=c++17 main.cpp $(fltk-config --cxxflags --ldflags) -o emulator
