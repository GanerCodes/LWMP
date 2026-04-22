FROM alpine:edge

RUN apk add --no-cache bash git make gcc g++ musl-dev libc-dev linux-headers \
    cmake ninja curl wget unzip tar ca-certificates openssl-dev zlib-dev libffi-dev \
    readline-dev sqlite-dev bzip2-dev xz-dev ncurses-dev fontforge fontforge-dev \
    nodejs npm udev eudev

# Build Python 3.14 (Alpine does not ship it)
ENV PYTHON_VERSION=3.14.0
RUN apk add --no-cache build-base linux-headers && \
    cd /tmp && \
    wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
    tar -xzf Python-${PYTHON_VERSION}.tgz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure --enable-optimizations --with-lto && \
    make -j$(nproc) && \
    make altinstall && \
    ln -sf /usr/local/bin/python3.14 /usr/local/bin/python && \
    ln -sf /usr/local/bin/pip3.14 /usr/local/bin/pip
RUN python -m ensurepip && pip install --no-cache-dir --upgrade pip setuptools wheel

# Clone LWMP
WORKDIR /opt
RUN git clone --recurse-submodules https://github.com/GanerCodes/LWMP.git
WORKDIR /opt/LWMP

RUN pip install --no-cache-dir esptool mpremote
# 󰤱 ↑ is temp
RUN pip install --no-cache-dir -r requirements.txt

# Install ☾
RUN git clone --depth 1 https://github.com/ganercodes/moon /opt/moon && \
    cd /opt/moon && \
    ./install

# ESP-IDF (expects Device/esp-idf tooling)
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