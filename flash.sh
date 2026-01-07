#!/bin/bash -e
{ cd "${0%/*}"

# yay --noconfirm --needed -S esptool rshell
# pip install mpy-cross
# https://github.com/v923z/micropython-builder/releases/tag/latest

DEVICE="/dev/${1-ttyACM0}" # ttyUSB0
WRITE_BAUD_RATE="2000000" # "460800"
INTERACT_BAUD_RATE="115200"
# BUILD_ROM="1"
# CLEAN_ROM="1"
# DO_FLASH="1"
CREDENTIALS=$(echo -e 'TheWarp\nWarpStorm2025\ntesting')
UUID="12345abc"

[[ -e "$DEVICE" ]] || { echo "Could not find ${DEVICE}!"
                        exit 1; }

sudo screen -XS Lightwave quit && sleep 0.1 || :
sudo killall rshell && sleep 0.1 || :

[[ $DO_FLASH ]] && { sudo esptool -p "${DEVICE}" -b "${WRITE_BAUD_RATE}" erase-flash &
                     flash_erase_pid=$!; }

[[ $BUILD_ROM ]] && ./Device/ROM/build.sh $([[ $CLEAN_ROM == "1" ]] && echo "-c")

set_safe_mode() {
  unalias . || :; export PATH="$PATH:/opt/esp-idf/tools"; source /opt/esp-idf/export.sh
  
  echo -en "key,type,encoding,value\nlightwave,namespace,,\nsafeboot,i,i32,${1-1}" > /tmp/safeboot_nvs.csv
  pushd /opt/esp-idf/components/nvs_flash/nvs_partition_generator/
    python nvs_partition_gen.py generate /tmp/safeboot_nvs.csv /tmp/safeboot_nvs.bin 0x4000
  	popd
  sudo esptool -p "${DEVICE}" -b "${WRITE_BAUD_RATE}" \
       --before default-reset --after hard-reset write-flash \
       --flash-mode dio --flash-size detect --flash-freq 80m \
       0x9000 /tmp/safeboot_nvs.bin; }

[[ $DO_FLASH ]] && {
  pushd ./Device/ROM/Out
    wait $flash_erase_pid
    sudo esptool -p "${DEVICE}" -b "${WRITE_BAUD_RATE}" \
         --before default-reset --after hard-reset write_flash \
         --flash-mode dio --flash-size detect --flash-freq 80m \
         0x1000 bootloader.bin 0x8000 partition-table.bin 0x10000 micropython.bin
    popd;
} || set_safe_mode 1

pushd ./Device/Onboard
  for f in *.py; do
    mpy-cross -o "./${f%.py}.mpy" -march=xtensawin "./$f"
  done
  sleep 0.1
  sudo mpremote connect "${DEVICE}" fs rm ':/*' || :
  sudo mpremote connect "${DEVICE}" fs cp *.mpy :
  # sudo mpremote connect "${DEVICE}" fs cp *.html : || :
  rm *.mpy || :
  [ -n "$CREDENTIALS" ] && {
    echo -n "$CREDENTIALS" > /tmp/credentials
    sudo mpremote connect "${DEVICE}" fs cp /tmp/credentials :/credentials
    rm /tmp/credentials; }
  [ -n "$UUID" ] && {
    echo -n "$UUID" > /tmp/UUID
    sudo mpremote connect "${DEVICE}" fs cp /tmp/UUID :/UUID
    rm /tmp/UUID; }
  sudo mpremote connect "${DEVICE}" fs cp boot._py :/boot.py
  set_safe_mode 0
  popd

echo Entering screen session
sudo screen -S Lightwave "${DEVICE}" "${INTERACT_BAUD_RATE}"
sudo screen -XS Lightwave quit

exit $?; }