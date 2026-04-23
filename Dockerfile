FROM debian:bookworm

# Install 6.875⨯10²⁶ deps
RUN apt-get update && apt-get install -y \
                        fontforge g++ gcc git libbz2-dev libdb5.3-dev \
                        bash build-essential ca-certificates cmake curl \
                        libexpat1-dev libffi-dev libgdbm-dev liblzma-dev \
                        libncurses5-dev libncursesw5-dev libreadline-dev \
                        libsqlite3-dev libssl-dev libudev-dev libusb-1.0-0 \
                        ninja-build nodejs npm python3 python3.11-venv make \
                        python3-pip tar tk-dev udev unzip uuid-dev wget zlib1g-dev \
                   && rm -rf /var/lib/apt/lists/*

# I hate him
RUN rm /usr/lib/python3.11/EXTERNALLY-MANAGED

# Install Python3.14
WORKDIR /usr/src
RUN wget https://www.python.org/ftp/python/3.14.0/Python-3.14.0.tgz \
    && tar -xzf Python-3.14.0.tgz \
    && cd Python-3.14.0 \
    && ./configure --enable-optimizations --prefix=/usr \
    && make -j$(nproc) \
    && make bininstall \
    && cp /bin/python3.14 /bin/python \
    && python -m ensurepip -U \
    && python -m pip install -U pip setuptools wheel

# Clone LWMP
RUN git clone --recursive --depth=1 https://github.com/GanerCodes/LWMP.git /opt/LWMP
WORKDIR /opt/LWMP

# Install esp-idf
ENV IDF_TOOLS_PATH=/root/.espressif
RUN cd Device/esp-idf && ./install.sh esp32

# Install ☾
RUN git clone --recursive --depth=1 https://github.com/ganercodes/moon /opt/moon \
    && /opt/moon/install

# Hack to force reupdate, 󰤱 just make it check git hash
RUN echo 1
RUN add-apt-repository ppa:fontforge/fontforge; apt-get update; apt-get install python3-fontforge

# Update LWMP and dependencies
RUN git pull \
    && pip install --no-cache-dir -r requirements.txt \
    && cp --remove-destination -r /opt/LWMP/Tools/jsbeautifier/ /usr/lib/python3.14/site-packages/ \
    && npm install -g lightningcss lightningcss-cli esbuild minify html-minifier-terser

CMD ["/bin/bash"]