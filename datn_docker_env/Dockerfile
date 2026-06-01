FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Ho_Chi_Minh
ENV ORFS_HOME=/opt/OpenROAD-flow-scripts
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
      libboost-all-dev \
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
      yosys || true

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
      gymnasium \
      stable-baselines3 \
      torch \
      torchvision \
      torchaudio

# OpenROAD:
# 1. Ưu tiên package apt nếu có.
# 2. Nếu không có, chỉ clone ORFS source để chuẩn bị, không tự build OpenROAD nặng từ source.
RUN if apt-cache show openroad >/dev/null 2>&1; then \
      apt-get update && apt-get install -y --no-install-recommends openroad; \
    else \
      echo "openroad package not available via apt on this base image"; \
    fi

RUN git clone --depth 1 https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git ${ORFS_HOME} || true

# DREAMPlace: clone source, không tự build vì còn phụ thuộc tương thích CUDA/PyTorch/GCC/CMake.
RUN git clone --depth 1 https://github.com/limbo018/DREAMPlace.git ${DREAMPLACE_HOME} || true

WORKDIR /workspace/DATN

CMD ["bash"]
