#!/bin/bash

{ cd "${0%/*}"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch origin
  H_OLD=$(git rev-parse @)
  H_NEW=$(git rev-parse @{u} 2>/dev/null || true)
  if [[ -n "${H_NEW}" && "${H_OLD}" != "${H_NEW}" ]]; then
    git pull --ff-only
    exec "$0" "$@"
  fi
fi

npm install -g lightningcss-cli esbuild minify html-minifier-terser
pip install -U lmdb aiohttp requests websockets esptool mpremote 'six>=1.13.0' 'editorconfig>=0.12.2'
cp --remove-destination -r ./Server/Tools/jsbeautifier/ /usr/lib/python3.14/site-packages

exit $?; }