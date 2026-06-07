ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Ho_Chi_Minh
ENV DREAMPLACE_HOME=/opt/DREAMPlace
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

SHELL ["/bin/bash", "-lc"]

RUN ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime && \
    echo "${TZ}" > /etc/timezone && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      git \
      wget \
      curl \
      ca-certificates \
      cmake \
      ninja-build \
      pkg-config \
      python3 \
      python3-pip \
      python3-dev \
      python3-venv \
      tcl \
      tcl-dev \
      tk \
      tk-dev \
      swig \
      bison \
      flex \
      libffi-dev \
      libreadline-dev \
      zlib1g-dev \
      libbz2-dev \
      liblzma-dev \
      libsqlite3-dev \
      libssl-dev \
      libboost-dev \
      libeigen3-dev \
      libspdlog-dev \
      libfmt-dev \
      libgtest-dev \
      graphviz \
      xauth \
      x11-apps \
      mesa-utils \
      libx11-6 \
      libxext6 \
      libxrender1 \
      libxtst6 \
      libxi6 \
      libxrandr2 \
      libxinerama1 \
      libxcursor1 \
      libglu1-mesa \
      tzdata \
      yosys && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir \
      numpy \
      scipy \
      pandas \
      matplotlib \
      networkx \
      tqdm \
      pyyaml \
      tensorboard \
      gymnasium && \
    python3 -m pip install --no-cache-dir \
      --index-url https://download.pytorch.org/whl/cpu \
      torch \
      torchvision \
      torchaudio && \
    python3 -m pip install --no-cache-dir --no-deps stable-baselines3

# DREAMPlace: clone source, không tự build vì còn phụ thuộc tương thích CUDA/PyTorch/GCC/CMake.
RUN git clone --depth 1 https://github.com/limbo018/DREAMPlace.git ${DREAMPLACE_HOME} || true

WORKDIR /workspace/DATN

CMD ["bash"]
