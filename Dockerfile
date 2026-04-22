FROM debian:bookworm

RUN apt-get update && apt-get install -y \
                        bash build-essential ca-certificates cmake curl \
                        fontforge g++ gcc git libbz2-dev libdb5.3-dev \
                        libexpat1-dev libffi-dev libgdbm-dev liblzma-dev \
                        libncurses5-dev libncursesw5-dev libreadline-dev \
                        libsqlite3-dev libssl-dev libudev-dev libusb-1.0-0 make \
                        ninja-build nodejs npm python3 python3.11-venv python3-fontforge \
                        python3-pip tar tk-dev udev unzip uuid-dev wget zlib1g-dev \
                   && rm -rf /var/lib/apt/lists/*

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

# Install Node Packages
RUN npm install -g lightningcss esbuild minify html-minifier-terser

# Install LWMP
RUN git clone --recursive --depth=1 https://github.com/GanerCodes/LWMP.git /opt/LWMP
WORKDIR /opt/LWMP
RUN python3.13 -m pip install --no-cache-dir -r requirements.txt

# ESP-IDF (expects Device/esp-idf tooling)
ENV IDF_TOOLS_PATH=/root/.espressif
RUN cd Device/esp-idf && ./install.sh esp32

# Install ☾
RUN git clone --recursive --depth=1 https://github.com/ganercodes/moon /opt/moon
RUN /opt/moon/install

# Install dumb bug fixed library
RUN cp -r /opt/LWMP/Tools/jsbeautifier /usr/lib/python3.13/site-packages/

# Update...
RUN git pull

CMD ["/bin/bash"]