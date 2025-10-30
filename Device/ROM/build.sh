#!/bin/bash -e
{ cd "${0%/*}"

SDKCONF="$(pwd)/sdkconfig"
PARTITIONS="$(pwd)/partitions.csv"
USERMODS="$(realpath ../Modules)"
NUM_CORES=15

unalias . || :
export PATH="$PATH:/opt/esp-idf/tools"
source /opt/esp-idf/export.sh

cd ../Micropython/ports/esp32
[[ " $* " == *" -c "* ]] && rm -rf build
cmake -B build -DUSER_C_MODULES="$USERMODS"
sed -i -e "s|^CONFIG_PARTITION_TABLE_CUSTOM_FILENAME=.*|CONFIG_PARTITION_TABLE_CUSTOM_FILENAME=\"$PARTITIONS\"|" \
       -e "s|^CONFIG_PARTITION_TABLE_FILENAME=.*|CONFIG_PARTITION_TABLE_FILENAME=\"$PARTITIONS\"|" \
       ./build/sdkconfig

pushd build
    make -j${NUM_CORES} EXTRA_CFLAGS="-Wno-error=parentheses"
    cp bootloader/bootloader.bin partition_table/partition-table.bin micropython.bin ../../../../ROM/Out
    popd

exit $?; }