#!/bin/bash -e
{ cd "${0%/*}"

# WRITE_BAUD_RATE="2000000"
WRITE_BAUD_RATE="460800"
DEV_FS="$(realpath ./Device/ROM/Out)/onboard"
DEVS=($(ls /dev | grep -E '.*tty(ACM|USB).*' | sed 's/tty/\/dev\/tty/'))

[[ $1 == "--single" ]] && {
  
  until [ -f /tmp/flash_flag ]; do
    sleep 0.05
    done
  [[ -f /tmp/flash_bad_flag ]] && exit 0 || :

  DEV="$2"
  UUID="$3"
  FLASH_ROM=$([[ $4 == 'y' ]] && echo -n y || echo -n)
  echo "Flashing ${DEV} - ${UUID:-"No UUID"}"
  pushd ./Device
    [[ -n "$FLASH_ROM" ]] && {
      pushd ./ROM/Out
        esptool -p "$DEV" -b "$WRITE_BAUD_RATE" erase-flash
        esptool -p "$DEV" -b "$WRITE_BAUD_RATE" --chip esp32            \
                --before default-reset --after hard-reset write-flash   \
                --flash-mode dio --flash-size 4MB --flash-freq 40m      \
                0x1000       bootloader.bin 0x8000  partition-table.bin \
                0xD000 ota_data_initial.bin 0x10000 micropython.bin
        popd; };
    pushd ./Onboard
      stty -F "$DEV" 115200 raw -echo
      for _ in {1..20}; do { printf '\x03'; sleep 0.05; } done > "$DEV"
      mpremote connect "$DEV" fs rm -r :/defaults/* || :
      mpremote connect "$DEV" fs cp -r ${DEV_FS}/* :/
      [[ -n "$UUID" ]] && {
        tmp=$(mktemp)
        echo "\"${UUID}\"" > "$tmp"
        mpremote connect "$DEV" fs cp "$tmp" :/UUID
        rm -f "$tmp"; }
      # exec mpremote connect "$DEV" reset
      exec mpremote connect "$DEV" run ./main._py; }

FLASH_ROM=$([[ $1 == 'y' ]] && echo -n y || echo -n)
BUILD_ROM=$([[ $2 == 'y' ]] && echo -n y || echo -n)
CLEAN_ROM=$([[ $3 == 'y' ]] && echo -n y || echo -n)
DEV_UUIDS=$([[ $4 == 'y' ]] && echo -n y || echo -n)
PRESET=${5:-"Normal"}
# echo [${FLASH_ROM}] [${BUILD_ROM}] [${CLEAN_ROM}] [${DEV_UUIDS}] [${PRESET}]

killall mpremote && sleep 0.05 || :
rm /tmp/flash_flag     || :
rm /tmp/flash_bad_flag || :

for i in "${!DEVS[@]}"; do
  dev="${DEVS[i]}"
  uuid=$([[ -n "$DEV_UUIDS" ]] && echo -n "testdevice${i}" || echo -n)
  
  echo "Spawning flasher for \"${dev}\""
  
  CMD=(bash "./$(basename "$0")" --single "$dev" "$uuid" "$FLASH_ROM")
  if [[ "$SYSTEM" == "desktop" ]]; then
    /c/Scripts/Path/term -T "(${i}) ${dev}" --option 'font.size=11' --command "${CMD[@]}" &
  else
    TARG="flash:main"
    tmux has-session -t "flash" 2>/dev/null || \
      tmux new-session -d -s "flash" -n main "${CMD[@]}"
    if [[ $i -ne 0 ]]; then
      tmux split-window -t "$TARG" -d "${CMD[@]}"
      tmux select-layout -t "$TARG" tiled
    fi
  fi
  
  done

unalias . || :; export PATH="$PATH:$PWD/Device/esp-idf"; source ./Device/esp-idf/export.sh

N=0
pushd ./Device
  [[ -n "$BUILD_ROM" ]] && { ./ROM/build.sh $([[ -n "$CLEAN_ROM" ]] && echo "-c") || bad=1; }
  
  [[ -n "$bad" ]] || {
    mkdir -p ${DEV_FS}   || :
    rm    -r ${DEV_FS}/* || :
    
    cp "./VERSION" "${DEV_FS}/VER"
    pushd ./Presets
      cp    ./Config/CERT.pem    "${DEV_FS}/CERT.pem"
      cp -r ./Config/${PRESET}/* "${DEV_FS}"
      cp -r ./Scenes             "${DEV_FS}/Scenes"
      popd
    pushd ./Onboard
      npx minify index.html > /tmp/index.min.html
      gzip -9 -c /tmp/index.min.html > "${DEV_FS}/index.html.gzip"
      
      cp main._py "${DEV_FS}/main.py"
      for f in *.py; do
        mpy-cross -o "${DEV_FS}/${f%.py}.mpy" -march=xtensawin "./$f" &
        N=`expr $N + 1`
        done
      popd
    pushd ./Module_Dynamic
      export CFLAGS="-Wno-error=unused-variable -Wno-error=unused-function -Wno-error=parentheses -Wno-error=maybe-uninitialized"
      make && { cp *.mpy "${DEV_FS}/"; } || { bad=1; }
      popd; }
  popd

for ((n=0; n < $N; n++)); do
  wait -n || bad=1
done
[[ -n "$bad" ]] && touch /tmp/flash_bad_flag || :
touch /tmp/flash_flag

if [[ "$SYSTEM" != "desktop" ]]; then
  tmux a -t flash
fi

exit $?; }