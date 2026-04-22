FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    openssh-server \
    sudo \
    xauth \
    x11-apps \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/sshd /etc/ssh/authorized_keys /workspace

RUN curl -L \
    https://github.com/Precision-Innovations/OpenROAD/releases/download/2024-12-14/openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb \
    -o /tmp/openroad.deb \
  && apt-get update \
  && apt-get install -y /tmp/openroad.deb \
  && rm -f /tmp/openroad.deb \
  && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash openroad \
  && echo "openroad ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/openroad

RUN sed -i 's/^#X11Forwarding yes/X11Forwarding yes/' /etc/ssh/sshd_config \
  && sed -i 's/^X11Forwarding no/X11Forwarding yes/' /etc/ssh/sshd_config \
  && printf '\nX11UseLocalhost no\nAllowTcpForwarding yes\nPubkeyAuthentication yes\nPasswordAuthentication no\nPermitRootLogin no\n' >> /etc/ssh/sshd_config

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 22

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
