FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-lc"]

ARG OSS_CAD_SUITE_URL="https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-04-21/oss-cad-suite-linux-x64-20260421.tgz"
ARG OPENROAD_DEB_URL="https://github.com/Precision-Innovations/OpenROAD/releases/download/2024-12-14/openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb"
ARG ORFS_REF="9f231560d3c024ff58eb7943c0906caa393eef95"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git \
      python3 \
      python3-pip \
      curl \
      wget \
      ca-certificates \
      make \
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
      python3-venv \
      tcl \
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

RUN curl -fL --retry 8 --retry-delay 5 --retry-all-errors "${OPENROAD_DEB_URL}" -o /tmp/openroad.deb && \
    apt-get update && \
    apt-get install -y --no-install-recommends /tmp/openroad.deb && \
    rm -f /tmp/openroad.deb && \
    ln -sf /usr/bin/openroad /usr/local/bin/openroad

RUN git init /opt/OpenROAD-flow-scripts && \
    cd /opt/OpenROAD-flow-scripts && \
    git remote add origin https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git && \
    git fetch --depth 1 origin "${ORFS_REF}" && \
    git checkout FETCH_HEAD

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
