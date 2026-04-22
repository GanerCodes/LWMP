#!/bin/bash -e
{ cd "${0%/*}"

PARTITIONS="$(pwd)/partitions.csv"
USERMODS="$(realpath ../Modules_Native)"
OUT_DIR="$(realpath ./Out)"
NUM_CORES=15

mkdir -p "$OUT_DIR"
unalias . || :; export PATH="$PATH:$PWD/../esp-idf"; source ../esp-idf/export.sh

pushd ../micropython
  pushd ports/esp32
    [[ " $* " == *" -c "* ]] && {
      rm -rf build-ESP32_GENERIC || :
      idf.py fullclean; }
    
    B="./boards/sdkconfig.base.original"
    T="./boards/sdkconfig.base"
    [[ ! -f "$B" ]] && cp "$T" "$B" || :
    { cat "$B"; echo "";
      echo "CONFIG_PARTITION_TABLE_CUSTOM=y"
      echo "CONFIG_PARTITION_TABLE_CUSTOM_FILENAME=\"${PARTITIONS}\""
      echo "CONFIG_MBEDTLS_MPI_MAX_SIZE=256"
      echo "CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN=4096"
      echo "CONFIG_MBEDTLS_SSL_IN_CONTENT_LEN=4096"
      echo "CONFIG_MBEDTLS_SSL_OUT_CONTENT_LEN=4096"
      echo "CONFIG_MBEDTLS_HAVE_TIME_DATE=n"
      # echo "CONFIG_MBEDTLS_SSL_MAX_FRAGMENT_LENGTH=y"
      # echo "CONFIG_MBEDTLS_DYNAMIC_BUFFER=y"
    } > "$T"
    
    { echo '#define MICROPY_HW_BOARD_NAME        "ESP32 LightWave"'
      echo '#define MICROPY_HW_MCU_NAME          "ESP32LW"        '
    } > "./boards/ESP32_GENERIC/mpconfigboard.h"
    popd
  
  make -C ports/esp32 BOARD=ESP32_GENERIC submodules
  make -C ports/esp32 EXTRA_CFLAGS="-DMICROPY_GC_INITIAL_HEAP_SIZE=53248 \
                                    -Wno-error=misleading-indentation \
                                    -Wno-error=maybe-uninitialized \
                                    -Wno-error=uninitialized \
                                    -Wno-error=unused-value \
                                    -Wno-error=parentheses" \
                      BOARD=ESP32_GENERIC USER_C_MODULES="$USERMODS"
  pushd ports/esp32/build-ESP32_GENERIC
    cp bootloader/bootloader.bin partition_table/partition-table.bin ota_data_initial.bin micropython.bin "$OUT_DIR"
    popd
  
  pushd mpy-cross
    make
    pushd build
      sudo cp mpy-cross /usr/bin/mpy-cross # LOL

exit $?; }