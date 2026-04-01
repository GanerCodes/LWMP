#!/bin/bash
# git clone --recursive --depth=1 https://github.com/micropython/micropython
git clone -b v5.5.1 --recursive --depth=1 https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32
