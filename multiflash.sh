#!/bin/bash -e
{ cd "${0%/*}"

# ChatGPT type script

sudo killall mpremote && sleep 0.1 || :

if [ "$#" -gt 0 ]; then
  devices=("$@")
else
  devices=($(find /dev/ttyUSB*) $(find /dev/ttyACM*))
fi

for i in "${!devices[@]}"; do
  dev="${devices[i]}"
  /c/Scripts/Path/term --option 'font.size=14' --command ./flash.sh "$dev" "testdevice$i" &
done

exit $?; }