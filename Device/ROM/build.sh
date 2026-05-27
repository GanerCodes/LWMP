#!/bin/bash -e
{ cd "${0%/*}"

      NUM_CORES="$(nproc)"
       USERMODS="$(realpath ../Modules_Native)"
      MPY_PORTS="$(realpath ../MPY_ports_custom)"
     PARTITIONS="$(pwd)/partitions.csv"
SDK_CONF_CUSTOM="$(pwd)/sdk_conf"
MPY_CONF_CUSTOM="$(pwd)/mpy_conf"
         Q_STRS="$(pwd)/q_strs"
        OUT_DIR="$(pwd)/Out"

mkdir -p "$OUT_DIR"
unalias . || :; export PATH="$PATH:$PWD/../esp-idf"; source ../esp-idf/export.sh

pushd ../micropython
  rm -r ./ports || :
  cp -r "$MPY_PORTS" ./ports
  pushd ports/esp32
    # [[ " $* " == *" -c "* ]] && {
    #   rm -rf build-LightWave || :
    #   idf.py fullclean; }
    
    cp "$MPY_CONF_CUSTOM" "./boards/LightWave/mpconfigboard.h"
    cp "$SDK_CONF_CUSTOM" "./boards/sdkconfig.base.original"
    cp "$Q_STRS"          "./qstrdefsport.h"
    B="./boards/sdkconfig.base.original"
    T="./boards/sdkconfig.base"
    [[ ! -f "$B" ]] && cp "$T" "$B" || :
    { cat "$B"; echo -e "\nCONFIG_PARTITION_TABLE_CUSTOM=y"
      echo "CONFIG_PARTITION_TABLE_CUSTOM_FILENAME=\"${PARTITIONS}\""; } > "$T"
    sed -i 's/^#define MP_TASK_COREID *(1)/#define MP_TASK_COREID (0)/' "./mphalport.h" # hack upon hack upon hacks
    popd
  
  # make -C ports/esp32 BOARD=LightWave submodules
  make -C ports/esp32 EXTRA_CFLAGS="-DMICROPY_GC_INITIAL_HEAP_SIZE=53248 \
                                    -Wno-error=misleading-indentation \
                                    -Wno-error=maybe-uninitialized \
                                    -Wno-error=uninitialized \
                                    -Wno-error=unused-value \
                                    -Wno-error=unused-label \
                                    -Wno-error=parentheses" \
                      BOARD=LightWave USER_C_MODULES="$USERMODS" # 󰤱 why is heapsize put here
  pushd ports/esp32/build-LightWave
    cp bootloader/bootloader.bin partition_table/partition-table.bin ota_data_initial.bin micropython.bin "$OUT_DIR"
    popd
  
  pushd mpy-cross
    make
    pushd build
      if [ "$EUID" -eq 0 ]; then
        cp mpy-cross /bin/mpy-cross
      else
        doas cp mpy-cross /bin/mpy-cross
      fi

exit $?; }