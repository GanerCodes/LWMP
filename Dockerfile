FROM debian:bookworm

RUN apt-get update && apt-get install -y \
                        bash git make gcc g++ cmake ninja-build \
                        curl wget unzip tar ca-certificates \
                        libssl-dev zlib1g-dev libffi-dev \
                        libreadline-dev libsqlite3-dev \
                        libbz2-dev liblzma-dev libncurses5-dev \
                        fontforge python3-fontforge \
                        nodejs npm udev \
                   && rm -rf /var/lib/apt/lists/*
# Clone LWMP
WORKDIR /opt
RUN git clone --recurse-submodules https://github.com/GanerCodes/LWMP.git
WORKDIR /opt/LWMP

RUN pip install --no-cache-dir -r requirements.txt

# Install ☾
RUN git clone --depth 1 https://github.com/ganercodes/moon /opt/moon && \
    cd /opt/moon && \
    ./install

# ESP-IDF (expects Device/esp-idf tooling)
ENV IDF_TOOLS_PATH=/root/.espressif
RUN cd Device/esp-idf && ./install.sh esp32

# Node stuff
RUN npm install -g npm && node -v && npm -v

# Entry script to ensure ESP-IDF env is loaded
RUN printf '%s\n' \
'#!/bin/bash' \
'set -e' \
'' \
'# ESP-IDF environment' \
'if [ -f "$PWD/Device/esp-idf/export.sh" ]; then' \
'  source "$PWD/Device/esp-idf/export.sh"' \
'fi' \
'' \
'exec "$@"' \
> /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]