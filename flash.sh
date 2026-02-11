#!/bin/bash -e
{ cd "${0%/*}"

WRITE_BAUD_RATE="2000000"
DEVS=($(find /dev -regextype posix-extended -regex '.*/tty(ACM|USB).*'))

[[ $1 == "--single" ]] && {
  
  until [ -f /tmp/flash_flag ]; do
    sleep 0.05
    done
  [[ -f /tmp/flash_bad_flag ]] && exit 0 || :

  DEV="$2"
  UUID="$3"
  FLASH_ROM=$([[ $4 == 'y' ]] && echo -n y || echo -n)
  echo "Flashing ${DEV} with UUID ${UUID}"
  pushd ./Device
    [[ -n "$FLASH_ROM" ]] && {
      pushd ./ROM/Out
        esptool -p "${DEV}" -b "${WRITE_BAUD_RATE}" erase-flash
        esptool -p "${DEV}" -b "${WRITE_BAUD_RATE}" --chip esp32        \
                --before default-reset --after hard-reset write-flash   \
                --flash-mode dio --flash-size 4MB --flash-freq 40m      \
                0x1000       bootloader.bin 0x8000  partition-table.bin \
                0xD000 ota_data_initial.bin 0x10000 micropython.bin
        popd; };
    pushd ./Onboard
      mpremote connect "${DEV}" fs rm       -r :/defaults/* || :
      mpremote connect "${DEV}" fs rm       -r :/defaults/* || : # 1st mpremote command fails sometimes ∵ weird thread stuff happening on esp32
      mpremote connect "${DEV}" fs cp compiled/*.mpy *.html :/
      mpremote connect "${DEV}" fs cp       -r ./defaults/* :/
      
      [[ -n "$UUID" ]] && {
        tmp=$(mktemp)
        echo "\"$UUID\"" >"$tmp"
        mpremote connect "${DEV}" fs cp "$tmp" :/UUID
        rm -f "$tmp"; }
      mpremote connect "${DEV}" fs cp main._py :/main.py
      exec mpremote connect "${DEV}" run ./main._py; }


FLASH_ROM=$([[ $1 == 'y' ]] && echo -n y || echo -n)
BUILD_ROM=$([[ $2 == 'y' ]] && echo -n y || echo -n)
CLEAN_ROM=$([[ $3 == 'y' ]] && echo -n y || echo -n)

killall mpremote && sleep 0.05 || :
rm /tmp/flash_flag || :
rm /tmp/flash_bad_flag || :

for i in "${!DEVS[@]}"; do
  dev="${DEVS[i]}"
  echo 1
  /c/Scripts/Path/term -T "${dev} (${i})" --option 'font.size=11' --command bash "./$(basename "$0")" --single "${dev}" "testdevice${i}" "${FLASH_ROM}" &
  done

unalias . || :; export PATH="$PATH:/opt/esp-idf/tools"; source /opt/esp-idf/export.sh

N=0
pushd ./Device
  [[ -n "$BUILD_ROM" ]] && {
      ./ROM/build.sh $([[ -n "$CLEAN_ROM" ]] && echo "-c") || bad=1; }
  
  [[ -n "$bad" ]] || {
    pushd ./Onboard
      mkdir -p compiled || :
      for f in *.py; do
        mpy-cross -o "./compiled/${f%.py}.mpy" -march=xtensawin "./$f" &
        N=`expr $N + 1`
        done
      pushd ../Module_Dynamic
        export CFLAGS="-Wno-error=unused-variable -Wno-error=unused-function -Wno-error=parentheses -Wno-error=maybe-uninitialized"
        make && {
          cp *.mpy ../Onboard/compiled
        } || { bad=1; }
        
        popd
      popd; };
  
  popd

for ((n=0; n < $N; n++)); do
  wait -n || bad=1
done
[[ -n "$bad" ]] && touch /tmp/flash_bad_flag || :
touch /tmp/flash_flag

exit $?; }