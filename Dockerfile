# Build python3.14
FROM debian:bookworm

RUN : && apt-get update \
      && apt-get install -y build-essential wget tar libssl-dev zlib1g-dev        \
                            libbz2-dev libreadline-dev libncurses-dev libffi-dev  \
                            liblzma-dev libgdbm-dev libgdbm-compat-dev libnsl-dev \
                            libexpat1-dev tk-dev uuid-dev                         \
      && rm -rf /var/lib/apt/lists/*
RUN : && wget https://www.python.org/ftp/python/3.14.0/Python-3.14.0.tgz \
      && tar -xzf Python-3.14.0.tgz \
      && cd Python-3.14.0 \
      && ./configure --prefix=/opt/python3.14 --enable-optimizations \
      && make -j$(nproc) \
      && make install

# The rest of the owl
FROM debian:bookworm

RUN : && apt-get update \
      && apt-get install -y ninja-build build-essential ccache libffi-dev      \
                            libssl-dev libusb-1.0-0 dfu-util pkg-config        \
                            flex bison gperf git tar bash curl tmux            \
                            udev make cmake npm nodejs tmux fontforge          \
                            python3 python3-pip python3-venv python3-fontforge \
      && rm -rf /var/lib/apt/lists/*
COPY --from=0 /opt/python3.14 /opt/python3.14
RUN : && ln -fs /opt/python3.14/bin/python3.14 /bin/python \
      && ln -fs /opt/python3.14/bin/pip3.14    /bin/pip    \
      && python -m ensurepip -U \
      && python -m pip install -U pip setuptools wheel
      && rm /usr/lib/python3.11/EXTERNALLY-MANAGED

# LWMP / ☾ / esp-idf
ENV IDF_TOOLS_PATH=/root/.espressif
RUN : && git clone --recursive --depth=1 https://github.com/GanerCodes/LWMP.git /opt/LWMP \
      && git clone --recursive --depth=1 https://github.com/ganercodes/moon /opt/moon \
      && /opt/moon/install \
      && cd /opt/LWMP/Device/esp-idf \
      && ./install.sh esp32

# Create entrypoint + update dependencies
WORKDIR /opt/LWMP
RUN : && /bin/echo -en '#!/bin/bash\ncd /opt/LWMP\n./deps.sh||:\nexec "$@"' > /entrypoint.sh \
      && chmod +x /entrypoint.sh \
      && ./deps.sh
ENTRYPOINT ["/entrypoint.sh"]