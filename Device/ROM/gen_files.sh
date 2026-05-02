#!/bin/bash -e
{ cd "${0%/*}/.."

DEV_FS="$(realpath ./ROM/Out)/onboard"
VER="${1:-$(cat "./VERSION")}"
PRESET="${2:-"Normal"}"

echo "Generating flash files (VER=$VER PRESET=$PRESET)"

export PATH="$PATH:./esp-idf"; source ./esp-idf/export.sh
mkdir -p ${DEV_FS}   || :
rm    -r ${DEV_FS}/* || :

N=0

python -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$VER" > "${DEV_FS}/VER"
pushd ./Presets
  certf="./Config/${PRESET}/CERT.pem"
  [[ -f "$certf" ]] || certf="./Config/CERT.pem"
  cp "$certf" "${DEV_FS}/CERT.pem"
  cp -r ./Config/${PRESET}/* "${DEV_FS}"
  cp -r ./Scenes             "${DEV_FS}/Scenes"
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
  export CFLAGS="-Wno-error=unused-variable -Wno-error=unused-function -Wno-error=parentheses -Wno-error=maybe-uninitialized"
  make && { cp *.mpy "${DEV_FS}/"; } || { bad=1; }
  popd

for ((n=0; n < $N; n++)); do
  wait -n || bad=1
done

[[ -n "$bad" ]] && exit 1 || exit 0

exit $?; }