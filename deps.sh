#!/bin/bash

{ cd "${0%/*}"

FLAG=~/.local/share/LWMP_deps_flag

install_deps() { npm install -g lightningcss-cli esbuild minify html-minifier-terser
                 pip install -U lmdb aiohttp requests websockets esptool mpremote \
                                'six>=1.13.0' 'editorconfig>=0.12.2'
                 cp --remove-destination -r ./Server/Tools/jsbeautifier/ \
                                             /opt/python3.14/lib/python3.14/site-packages
                 mkdir -p "$(dirname "$FLAG")"
                 touch "$FLAG" || :; }

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch origin
  H_OLD=$(git rev-parse @)
  H_NEW=$(git rev-parse @{u} 2>/dev/null || true)
  echo "${H_OLD} → ${H_NEW}"
  if [[ -n "${H_NEW}" && "${H_OLD}" != "${H_NEW}" ]]; then
    rm "$FLAG" || :
    git pull --ff-only
    exec "$0" "$@"
  fi
fi

[ -f "$FLAG" ] || install_deps

exit $?; }