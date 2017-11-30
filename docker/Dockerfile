FROM il2horusteam/il2ds:latest

RUN \
    export LANGUAGE="en_US.UTF-8" \
 && export LANG="en_US.UTF-8" \
 && export LC_ALL="en_US.UTF-8" \
 && locale-gen "en_US.UTF-8" \
 && dpkg-reconfigure --frontend=noninteractive locales \
 && add-apt-repository -y ppa:deadsnakes/ppa \
 && apt update \
 && apt install -y --no-install-recommends \
    gcc \
    git \
    python3.6 \
    python3.6-dev \
 && wget -qO- https://bootstrap.pypa.io/get-pip.py | python3.6 \
 && pip3 install \
      git+https://github.com/IL2HorusTeam/il2fb-ds-config.git \
      git+https://github.com/IL2HorusTeam/il2fb-mission-parser.git \
      git+https://github.com/IL2HorusTeam/il2fb-game-log-parser.git \
      git+https://github.com/IL2HorusTeam/il2fb-ds-middleware.git \
      git+https://github.com/IL2HorusTeam/il2fb-ds-airbridge.git \
 && mkdir -p /etc/airbridge \
 && mkdir -p /var/log/airbridge

COPY confs.ini /il2ds/confs.ini
COPY airbridge.yml /etc/airbridge/airbridge.yml

WORKDIR /il2ds

CMD ["il2fb-ds-airbridge", "-c", "/etc/airbridge/airbridge.yml"]
