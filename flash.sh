#!/bin/bash -e
{ cd "${0%/*}"

# yay --noconfirm --needed -S esptool
# sudo pip install mpy-cross mpremote
# https://github.com/v923z/micropython-builder/releases/tag/latest

DEVICE="/dev/${1-ttyACM0}" # ttyUSB0
WRITE_BAUD_RATE="2000000" # "460800"
INTERACT_BAUD_RATE="115200"
# BUILD_ROM="1"
# CLEAN_ROM="1"
# DO_FLASH="1"

[[ -e "$DEVICE" ]] || { echo "Could not find ${DEVICE}!"
                        exit 1; }

sudo screen -XS Lightwave quit && sleep 0.1 || :
sudo killall mpremote && sleep 0.1 || :

[[ $DO_FLASH ]] && { sudo esptool -p "${DEVICE}" -b "${WRITE_BAUD_RATE}" erase-flash &
                     flash_erase_pid=$!; }

[[ $BUILD_ROM ]] && ./Device/ROM/build.sh $([[ $CLEAN_ROM == "1" ]] && echo "-c")



[[ $DO_FLASH ]] && {
  pushd ./Device/ROM/Out
    wait $flash_erase_pid
    sudo esptool -p "${DEVICE}" -b "${WRITE_BAUD_RATE}" \
         --before default-reset --after hard-reset write_flash \
         --flash-mode dio --flash-size detect --flash-freq 80m \
         0x1000 bootloader.bin 0x8000 partition-table.bin 0x10000 micropython.bin
    popd; }

pushd ./Device/Onboard
  for f in *.py; do
    mpy-cross -o "./${f%.py}.mpy" -march=xtensawin "./$f"
  done
  sudo mpremote connect "${DEVICE}" fs rm -r :/ || :
  sudo mpremote connect "${DEVICE}" fs cp *.mpy *.html :/
  sudo mpremote connect "${DEVICE}" fs cp ./defaults/* :/
  sudo mpremote connect "${DEVICE}" fs cp main._py :/main.py
  rm *.mpy || :
  popd

echo Entering REPL
sudo mpremote connect "${DEVICE}"

exit $?; }