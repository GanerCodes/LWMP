#!/bin/bash -e
{ cd "${0%/*}"

shopt -s nullglob

VER=${1:?Usage: $0 <version> <preset?>}
PRESET="${2:-"Normal"}"

mkdir "${VER}" || { echo "Version \"${VER}\" already exists!"
                    exit 1; }

../Device/ROM/gen_files.sh "$VER" "$PRESET"

files=(../Device/ROM/Out/onboard/{*.mpy,*.py,*.gz,*.pem})
for f in "${files[@]}"; do cp "${f}" "${VER}/"; done
files=("${files[@]##*/}")
printf "%s" "$(printf "%s\n" "${files[@]}")" | jq -Rs 'split("\n")' > "${VER}/index.json"

echo -n "$VER" > ../Device/VERSION
echo "Created version ${VER}!"

exit $?; }