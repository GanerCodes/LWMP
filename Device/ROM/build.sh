#!/bin/bash -e
{ cd "${0%/*}"

SDKCONF="$(pwd)/sdkconfig"
PARTITIONS="$(pwd)/partitions.csv"
USERMODS="$(realpath ../Modules)"
NUM_CORES=15

# /opt/esp-idf/install.sh esp32
unalias . || :; export PATH="$PATH:/opt/esp-idf/tools"; source /opt/esp-idf/export.sh

cd ../Micropython/ports/esp32
[[ " $* " == *" -c "* ]] && rm -rf build
cmake -B build -DUSER_C_MODULES="$USERMODS"
sed -i -e "s|^CONFIG_PARTITION_TABLE_CUSTOM_FILENAME=.*|CONFIG_PARTITION_TABLE_CUSTOM_FILENAME=\"$PARTITIONS\"|" \
       -e "s|^CONFIG_PARTITION_TABLE_FILENAME=.*|CONFIG_PARTITION_TABLE_FILENAME=\"$PARTITIONS\"|" \
       ./build/sdkconfig
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

pushd build
  make -j${NUM_CORES} EXTRA_CFLAGS="-Wno-error=parentheses"
  cp bootloader/bootloader.bin partition_table/partition-table.bin micropython.bin ../../../../ROM/Out
  popd

exit $?; }