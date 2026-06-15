FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-lc"]

ARG OSS_CAD_SUITE_URL="https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-04-21/oss-cad-suite-linux-x64-20260421.tgz"
ARG BAZELISK_VERSION="1.28.1"
ARG OPENROAD_REF="master"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      git \
      cmake \
      ninja-build \
      python3 \
      python3-pip \
      tcl \
      pkg-config \
      curl \
      wget \
      ca-certificates \
      xauth \
      x11-apps \
      libx11-6 \
      libxext6 \
      libxrender1 \
      libxtst6 \
      libxi6 \
      libxrandr2 \
      libxinerama1 \
      libxcursor1 \
      libxcb-cursor0 \
      libglu1-mesa \
      mesa-utils \
      graphviz \
      make \
      bison \
      flex \
      swig \
      zip \
      unzip \
      python3-venv \
      python3-dev \
      libboost-all-dev \
      openjdk-21-jre-headless \
      locales && \
    locale-gen en_US.UTF-8 && \
    update-ca-certificates

RUN set -e; \
    if apt-cache show klayout >/dev/null 2>&1; then \
      apt-get install -y --no-install-recommends klayout; \
    else \
      echo "klayout package not available in apt for this base image"; \
    fi

RUN mkdir -p /opt/oss-cad-suite && \
    curl -fL --retry 8 --retry-delay 5 --retry-all-errors "${OSS_CAD_SUITE_URL}" -o /tmp/oss-cad-suite.tgz && \
    tar -xzf /tmp/oss-cad-suite.tgz -C /opt/oss-cad-suite --strip-components=1 && \
    rm -f /tmp/oss-cad-suite.tgz && \
    ln -sf /opt/oss-cad-suite/bin/yosys /usr/local/bin/yosys && \
    ln -sf /opt/oss-cad-suite/bin/yosys-abc /usr/local/bin/yosys-abc && \
    ln -sf /opt/oss-cad-suite/bin/yosys-abc /usr/local/bin/abc

RUN curl -fL "https://github.com/bazelbuild/bazelisk/releases/download/v${BAZELISK_VERSION}/bazelisk-linux-amd64" \
      -o /usr/local/bin/bazelisk && \
    chmod +x /usr/local/bin/bazelisk && \
    ln -sf /usr/local/bin/bazelisk /usr/local/bin/bazel

RUN git clone --recursive --depth 1 --branch "${OPENROAD_REF}" \
      https://github.com/The-OpenROAD-Project/OpenROAD.git /opt/OpenROAD-src && \
    cd /opt/OpenROAD-src && \
    bazelisk run --config=release --//:platform=gui //:install -- /opt/OpenROAD-install && \
    ln -sf /opt/OpenROAD-install/openroad /usr/local/bin/openroad

RUN git clone --depth 1 https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git /opt/OpenROAD-flow-scripts || true

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV ORFS_ROOT=/opt/OpenROAD-flow-scripts
ENV OPENROAD_EXE=/usr/local/bin/openroad
ENV YOSYS_EXE=/opt/oss-cad-suite/bin/yosys
ENV PATH=/opt/oss-cad-suite/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
WORKDIR /workspace

CMD ["bash"]
