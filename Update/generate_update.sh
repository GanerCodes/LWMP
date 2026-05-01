#!/bin/bash -e
{ cd "${0%/*}"

shopt -s nullglob

VERSION=${1:?Usage: $0 <version>}
mkdir "${VERSION}" || {
  echo "Version \"${VERSION}\" already exists!"
  exit 1; }

files=(../Device/ROM/Out/onboard/{*.mpy,*.py,*.gz,*.pem})
for f in "${files[@]}"; do cp "${f}" "${VERSION}/"; done
files=("${files[@]##*/}")
printf "%s" "$(printf "%s\n" "${files[@]}")" | jq -Rs 'split("\n")' > "${VERSION}/index.json"

echo -n "${VERSION}" > ../Device/VERSION
echo "Created version ${VERSION}!"

exit $?; }