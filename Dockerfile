FROM debian:bookworm

RUN apt-get update && apt-get install -y \
                        bash build-essential ca-certificates cmake curl \
                        fontforge g++ gcc git libbz2-dev libdb5.3-dev \
                        libexpat1-dev libffi-dev libgdbm-dev liblzma-dev \
                        libncurses5-dev libncursesw5-dev libreadline-dev \
                        libsqlite3-dev libssl-dev make ninja-build nodejs \
                        npm python3 python3-fontforge python3-pip tar tk-dev \
                        udev unzip uuid-dev wget zlib1g-dev \
                   && rm -rf /var/lib/apt/lists/*

# Install Node Packages
RUN npm install -g lightningcss esbuild minify

# Install Python3.13
WORKDIR /usr/src
RUN wget https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz && \
    tar -xzf Python-3.13.0.tgz && \
    cd Python-3.13.0 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall
RUN python3.13 -m ensurepip --upgrade && \
    python3.13 -m pip install --upgrade pip setuptools wheel
RUN rm /usr/lib/python3.11/EXTERNALLY-MANAGED

# Install ☾
RUN git clone --depth 1 https://github.com/ganercodes/moon /opt/moon
RUN /opt/moon/install

# Install LWMP
RUN git clone --recurse-submodules https://github.com/GanerCodes/LWMP.git /opt/LWMP
WORKDIR /opt/LWMP
RUN python3.13 -m pip install --no-cache-dir -r requirements.txt

# ESP-IDF (expects Device/esp-idf tooling)
ENV IDF_TOOLS_PATH=/root/.espressif
RUN cd Device/esp-idf && ./install.sh esp32

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