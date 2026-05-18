#!/bin/bash -e
{ cd "${0%/*}/.."

DEV_FS="$(realpath ./ROM/Out)/onboard"

VER="$(cat "./VERSION")"
PRESET="Normal"
CONFIG_INJ='{}'
SCENES_INJ='{}'
if [ $# -gt 0 ]; then
  [ -n "$1" ] && VER="$1"
  shift; fi
if [ $# -gt 0 ]; then
  [ -n "$1" ] && PRESET="$1"
  shift; fi
if [ $# -gt 0 ]; then
  [ -n "$1" ] && CONFIG_INJ="$1"
  shift; fi
if [ $# -gt 0 ]; then
  [ -n "$1" ] && SCENES_INJ="$1"
  shift; fi

echo "Generating flash files (VER=$VER PRESET=$PRESET)"

export PATH="$PATH:./esp-idf"; source ./esp-idf/export.sh
mkdir -p ${DEV_FS}   || :
rm    -r ${DEV_FS}/* || :

N=0
pushd ./Presets
  certf="./Config/${PRESET}/CERT.pem"
  [[ -f "$certf" ]] || certf="./Config/CERT.pem"
  cp "$certf" "${DEV_FS}/CERT.pem"
  cp -r ./Config/${PRESET}/* "${DEV_FS}"
  cp -r ./Scenes             "${DEV_FS}/Scenes"
  
  python -c '
from json import loads as L, dumps as D
from sys import argv as 𝔸
del 𝔸[0]
print(f"[{"|".join(𝔸)}]")
o = { "VER":D(𝔸[1]),
      **L(𝔸[2]),
      **{f"Scenes/{k}":v for k,v in L(𝔸[3]).items()} }
for k,v in o.items():
  with open(f"{𝔸[0]}/{k}","w") as f:
    f.write(str(v))
  ' "$DEV_FS" "$VER" "$CONFIG_INJ" "$SCENES_INJ"
  popd
pushd ./Onboard
  npx minify index.html > /tmp/index.min.html
  gzip -9 -c /tmp/index.min.html > "${DEV_FS}/index.html.gz"
  
  cp main._py "${DEV_FS}/main.py"
  for f in *.py; do
    mpy-cross -o "${DEV_FS}/${f%.py}.mpy" -march=xtensawin "./$f" &
    N=`expr $N + 1`
    done
  popd
pushd ./Module_Dynamic
  rm -r build .mpy_ld_cache || :
  export CFLAGS="-Wno-error=unused-variable -Wno-error=unused-function -Wno-error=parentheses -Wno-error=maybe-uninitialized \
                 -Wno-unused-variable       -Wno-unused-function       -Wno-parentheses       -Wno-maybe-uninitialized"
  make && { cp *.mpy "${DEV_FS}/"; } || { bad=1; }
  rm -r build .mpy_ld_cache || :
  popd

for ((n=0; n < $N; n++)); do
  wait -n || bad=1
done

[[ -n "$bad" ]] && exit 1 || exit 0

exit $?; }