#!/bin/bash -e
{ cd "${0%/*}"

# yay --noconfirm --needed -S esptool
# sudo pip install mpy-cross mpremote
# https://github.com/v923z/micropython-builder/releases/tag/latest
# 󷹇 be part of group `uucp` so you can interface w/ microcontroller!

: || { # 󷹇²𝕊
  cd /home/ganer/Projects/Brynic/LWMP/Device/Micropython/ports/esp32/build-ESP32_GENERIC
  unalias . || :; export PATH="$PATH:/opt/esp-idf/tools"; source /opt/esp-idf/export.sh
  xtensa-esp32-elf-addr2line -pfiaC -e micropython.elf Backtrace: 0x400f7571:0x3ffde600 0x4012b92a:0x3ffde620 0x4009d993:0x3ffde650 0x400f8f9f:0x3ffde710 0x40100195:0x3ffde730 0x4012b8d5:0x3ffde750 0x4009ddaf:0x3ffde770 0x4009dbc4:0x3ffde870 0x40100195:0x3ffde890 0x4012c423:0x3ffde8b0 0x4012c46d:0x3ffde8f0 0x40100195:0x3ffde910 0x40128fb8:0x3ffde930 0x4011aebd:0x3ffde9d0
}

# DEVICE="/dev/${1-ttyACM0}" # ttyUSB0
DEVICE="${1-ttyUSB0}" # ttyUSB0
UUID="$2"
WRITE_BAUD_RATE="2000000" # "460800"
INTERACT_BAUD_RATE="115200"
# DO_FLASH="1"
# BUILD_ROM="1"
# CLEAN_ROM="1"

[[ -e "$DEVICE" ]] || { echo "Could not find ${DEVICE}!"
                        exit 1; }

# sudo screen -XS Lightwave quit && sleep 0.1 || :
# sudo killall mpremote && sleep 0.1 || :

[[ $DO_FLASH ]] && { esptool -p "${DEVICE}" -b "${WRITE_BAUD_RATE}" erase-flash &
                     flash_erase_pid=$!; }

pushd ./Device
  [[ $BUILD_ROM ]] && ./ROM/build.sh $([[ $CLEAN_ROM == "1" ]] && echo "-c")
  [[ $DO_FLASH  ]] && {
    pushd ./ROM/Out
      wait $flash_erase_pid
      esptool -p "${DEVICE}" -b "${WRITE_BAUD_RATE}" \
              --chip esp32 \
              --before default-reset --after hard-reset write-flash \
              --flash-mode dio --flash-size 4MB --flash-freq 40m \
              0x1000       bootloader.bin 0x8000  partition-table.bin \
              0xD000 ota_data_initial.bin 0x10000 micropython.bin 
      popd; }
  pushd ./Onboard
    mkdir compiled || :
    for f in *.py; do
      mpy-cross -o "./compiled/${f%.py}.mpy" -march=xtensawin "./$f" &
    done; wait
    
    # mpremote connect "${DEVICE}" fs rm -r :/ || :
    mpremote connect "${DEVICE}" fs rm       -r :/defaults/* || :
    mpremote connect "${DEVICE}" fs rm       -r :/defaults/* || :
    mpremote connect "${DEVICE}" fs cp compiled/*.mpy *.html :/
    mpremote connect "${DEVICE}" fs cp       -r ./defaults/* :/
    if [[ -n $UUID ]]; then
      tmp=$(mktemp)
      echo "\"$UUID\"" >"$tmp"
      mpremote connect "${DEVICE}" fs cp "$tmp" :/UUID
      rm -f "$tmp"
    fi
    mpremote connect "${DEVICE}" fs cp main._py :/main.py
    popd
  popd

echo "Booting LightWave"
mpremote connect "${DEVICE}" run ./Device/Onboard/main._py

exit $?; }