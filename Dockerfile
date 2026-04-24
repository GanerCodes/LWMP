FROM debian:bookworm

# Install 6.875⨯10²⁶ deps
RUN apt-get update && apt-get install -y \
                        g++ gcc git npm tar bash curl make udev tmux wget \
                        cmake unzip nodejs tk-dev python3 uuid-dev fontforge \
                        libbz2-dev libffi-dev libssl-dev zlib1g-dev libgdbm-dev \
                        liblzma-dev libudev-dev ninja-build python3-pip \
                        libdb5.3-dev libusb-1.0-0 libexpat1-dev libsqlite3-dev \
                        build-essential ca-certificates libncurses5-dev \
                        libreadline-dev python3.11-venv libncursesw5-dev \
                        python3-fontforge \
                   && rm -rf /var/lib/apt/lists/*

# Build python
RUN rm /usr/lib/python3.11/EXTERNALLY-MANAGED \
    && wget https://www.python.org/ftp/python/3.14.0/Python-3.14.0.tgz \
    && tar -xzf Python-3.14.0.tgz \
    && cd Python-3.14.0 \
    && ./configure --enable-optimizations --prefix=/usr \
    && make -j$(nproc) \
    && make bininstall \
    && cp /bin/python3.14 /bin/python \
    && python -m ensurepip -U \
    && python -m pip install -U pip setuptools wheel

# LWMP / ☾ / esp-idf
ENV IDF_TOOLS_PATH=/root/.espressif
RUN git clone --recursive --depth=1 https://github.com/GanerCodes/LWMP.git /opt/LWMP
    && git clone --recursive --depth=1 https://github.com/ganercodes/moon /opt/moon \
    && /opt/moon/install
    && cd /opt/LWMP/Device/esp-idf
    && ./install.sh esp32

# Create entrypoint + update dependencies
WORKDIR /opt/LWMP
RUN echo -en '#!/bin/bash\ncd /opt/LWMP\n./deps.sh||:\nexec "$@"' > /entrypoint.sh \
    && chmod +x /entrypoint.sh \
    && ./deps.sh
ENTRYPOINT ["/entrypoint.sh"]