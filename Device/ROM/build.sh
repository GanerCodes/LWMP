#!/bin/bash -e
{ cd "${0%/*}"

PARTITIONS="$(pwd)/partitions.csv"
USERMODS="$(realpath ../Modules)"
OUT_DIR="$(realpath ./Out)"
NUM_CORES=15

# /opt/esp-idf/install.sh esp32
mkdir -p "$OUT_DIR"
unalias . || :; export PATH="$PATH:/opt/esp-idf/tools"; source /opt/esp-idf/export.sh

pushd ../Micropython
  pushd ports/esp32
    [[ " $* " == *" -c "* ]] && rm -rf build-ESP32_GENERIC || :
    
    B="./boards/sdkconfig.base.original"
    T="./boards/sdkconfig.base"
    [[ ! -f "$B" ]] && cp "$T" "$B" || :
    { cat "$B"; echo "";
      echo "CONFIG_PARTITION_TABLE_CUSTOM=y"
      echo "CONFIG_PARTITION_TABLE_CUSTOM_FILENAME=\"${PARTITIONS}\""
    } > "$T"
    
    { echo '#define MICROPY_HW_BOARD_NAME "ESP32 LightWave"'
      echo '#define MICROPY_HW_MCU_NAME   "ESP32LW"        '
    } > "./boards/ESP32_GENERIC/mpconfigboard.h"
    popd
  
  make -C ports/esp32 BOARD=ESP32_GENERIC submodules
  make -C ports/esp32 EXTRA_CFLAGS="-Wno-error=parentheses -Wno-error=maybe-uninitialized" \
                      BOARD=ESP32_GENERIC
                      # USER_C_MODULES="$USERMODS" \
  pushd ports/esp32/build-ESP32_GENERIC
    cp bootloader/bootloader.bin partition_table/partition-table.bin ota_data_initial.bin micropython.bin "$OUT_DIR"
    popd
  popd

#  -e 's/^CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN=.*/CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN=2048/' \
#  -e 's/^CONFIG_MBEDTLS_MPI_MAX_SIZE=.*/CONFIG_MBEDTLS_MPI_MAX_SIZE=1024/' \
#  -e 's/^CONFIG_MBEDTLS_SSL_IN_CONTENT_LEN=.*/CONFIG_MBEDTLS_SSL_IN_CONTENT_LEN=2048/' \
#  -e 's/^CONFIG_MBEDTLS_SSL_OUT_CONTENT_LEN=.*/CONFIG_MBEDTLS_SSL_OUT_CONTENT_LEN=2048/' \
#  -e 's/^CONFIG_MBEDTLS_DEBUG=.*/# CONFIG_MBEDTLS_DEBUG is not set/' \
#  -e 's/^CONFIG_MBEDTLS_PSK_MODES=.*/# CONFIG_MBEDTLS_PSK_MODES is not set/' \
#  -e 's/^CONFIG_MBEDTLS_ECP_DP_SECP384R1_ENABLED=.*/# CONFIG_MBEDTLS_ECP_DP_SECP384R1_ENABLED is not set/' \
#  -e 's/^CONFIG_MBEDTLS_ECP_DP_SECP521R1_ENABLED=.*/# CONFIG_MBEDTLS_ECP_DP_SECP521R1_ENABLED is not set/' \
#  -e 's/^CONFIG_MBEDTLS_SSL_KEEP_PEER_CERTIFICATE=.*/# CONFIG_MBEDTLS_SSL_KEEP_PEER_CERTIFICATE is not set/' \
#  -e 's/^CONFIG_MBEDTLS_CERTIFICATE_BUNDLE=.*/# CONFIG_MBEDTLS_CERTIFICATE_BUNDLE is not set/' \

exit $?; }