#!/bin/bash -e
{ cd "${0%/*}"

# yay --noconfirm --needed -S esptool rshell
# pip install mpy-cross
# https://github.com/v923z/micropython-builder/releases/tag/latest

DEVICE="/dev/${1-ttyACM1}" # ttyUSB0
WRITE_BAUD_RATE="2000000" # "460800"
INTERACT_BAUD_RATE="115200"
BUILD_ROM="1"
# CLEAN_ROM="1"
DO_FLASH="1"
CREDENTIALS=$(echo -e 'TheWarp\nWarpStorm2025\ntesting')
UUID="12345abc"

[[ -e "$DEVICE" ]] || { echo "Could not find ${DEVICE}!"
                        exit 1; }

sudo screen -XS Lightwave quit && sleep 0.1 || :
sudo killall rshell && sleep 0.1 || :

[[ $DO_FLASH ]] && { sudo esptool -p "${DEVICE}" -b "${WRITE_BAUD_RATE}" erase-flash &
                     flash_erase_pid=$!; }

[[ $BUILD_ROM ]] && ./Device/ROM/build.sh $([[ $CLEAN_ROM == "1" ]] && echo "-c")

[[ $DO_FLASH ]] && {
    pushd ./Device/ROM/Out
        wait $flash_erase_pid
        sudo esptool -p "${DEVICE}" -b "${WRITE_BAUD_RATE}" \
            --before default-reset --after hard-reset write-flash \
            --flash-mode dio --flash-size detect --flash-freq 80m \
            0x1000 bootloader.bin 0x8000 partition-table.bin 0x10000 micropython.bin
        popd; }

pushd ./Device/Onboard
    sudo rshell -b "${INTERACT_BAUD_RATE}" -p "${DEVICE}" rm /pyboard/*
    for f in *.py; do
        mpy-cross -o "./${f%.py}.mpy" -march=xtensawin "./$f"
    done
    sudo rshell -b "${INTERACT_BAUD_RATE}" -p "${DEVICE}" cp *.mpy /pyboard
    # sudo rshell -b "${INTERACT_BAUD_RATE}" -p "${DEVICE}" cp *.{mpy,html,template} /pyboard
    rm *.mpy || :
    # [ -n "$CREDENTIALS" ] && {
    #     echo -n "$CREDENTIALS" > /tmp/credentials
    #     sudo rshell -b "${INTERACT_BAUD_RATE}" -p "${DEVICE}" cp /tmp/credentials /pyboard/credentials
    #     rm /tmp/credentials; }
    # [ -n "$UUID" ] && {
    #     echo -n "$UUID" > /tmp/UUID
    #     sudo rshell -b "${INTERACT_BAUD_RATE}" -p "${DEVICE}" cp /tmp/UUID /pyboard/UUID
    #     rm /tmp/UUID; }
    sudo rshell -b "${INTERACT_BAUD_RATE}" -p "${DEVICE}" cp boot._py /pyboard/boot.py
    popd

# echo Press enter to enter Screen session ; read

sudo screen -S Lightwave "${DEVICE}" "${INTERACT_BAUD_RATE}"
sudo screen -XS Lightwave quit

exit $?; }