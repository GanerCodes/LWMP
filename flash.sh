#!/bin/bash -e
{ cd "${0%/*}"

# yay --noconfirm --needed -S esptool
# sudo pip install mpy-cross mpremote
# https://github.com/v923z/micropython-builder/releases/tag/latest
# 󷹇 be part of group `uucp` so you can interface w/ microcontroller!

DEVICE="/dev/${1-ttyACM0}" # ttyUSB0
WRITE_BAUD_RATE="2000000" # "460800"
INTERACT_BAUD_RATE="115200"
BUILD_ROM="1"
# CLEAN_ROM="1"
DO_FLASH="1"

[[ -e "$DEVICE" ]] || { echo "Could not find ${DEVICE}!"
                        exit 1; }

sudo screen -XS Lightwave quit && sleep 0.1 || :
sudo killall mpremote && sleep 0.1 || :

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
    for f in *.py; do
      mpy-cross -o "./${f%.py}.mpy" -march=xtensawin "./$f"
    done
    # mpremote connect "${DEVICE}" fs rm -r :/ || :
    mpremote connect "${DEVICE}" fs cp -r :/defaults/* || :
    mpremote connect "${DEVICE}" fs cp *.mpy *.html :/
    mpremote connect "${DEVICE}" fs cp -r ./defaults/* :/
    mpremote connect "${DEVICE}" fs cp main._py :/main.py
    rm *.mpy || :
    popd
  popd

echo "Booting LightWave"
mpremote connect "${DEVICE}" run ./Device/Onboard/main._py

exit $?; }