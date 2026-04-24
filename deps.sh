#!/bin/bash

{ cd "${0%/*}"

FLAG=~/.local/share/LWMP_deps_flag
mkdir -p "$(dirname FLAG)" 

pull_deps() { npm install -g lightningcss-cli esbuild minify html-minifier-terser
              pip install -U lmdb aiohttp requests websockets esptool mpremote \
                             'six>=1.13.0' 'editorconfig>=0.12.2'
              cp --remove-destination -r ./Server/Tools/jsbeautifier/ \
                                          /usr/lib/python3.14/site-packages
              touch "$FLAG"; }

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch origin
  H_OLD=$(git rev-parse @)
  H_NEW=$(git rev-parse @{u} 2>/dev/null || true)
  echo "${H_OLD} → ${H_NEW}"
  if [[ -n "${H_NEW}" && "${H_OLD}" != "${H_NEW}" ]]; then
    rm "$FLAG"
    git pull --ff-only
    exec "$0" "$@"
  fi
fi

[ -f "$FLAG" ] || pull_deps

exit $?; }