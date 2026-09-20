FROM debian:bookworm-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/opt/engine/src

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates chromium fonts-dejavu-core tesseract-ocr=5.3.0-2 tesseract-ocr-eng=1:4.1.0-2 \
    openbox scrot x11-utils xauth xvfb \
    python3 python3-dev python3-tk python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY infra/desktop/requirements.lock /opt/desktop/requirements.lock
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir --require-hashes -r /opt/desktop/requirements.lock \
    && useradd --create-home --uid 1000 desktop \
    && mkdir /artifacts /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix \
    && chown desktop:desktop /artifacts \
    && dpkg-query -W > /opt/desktop/system-packages.txt

COPY infra/desktop/*.py /opt/desktop/
COPY infra/desktop/chromium-policy.json /etc/chromium/policies/managed/interface-ai.json
COPY engine /opt/engine/
COPY capabilities /opt/capabilities/
COPY . /build-source
RUN python /build-source/infra/desktop/build_manifest.py /build-source /opt/build-manifest.json \
    && rm -rf /build-source
USER desktop
WORKDIR /home/desktop
EXPOSE 6081
ENTRYPOINT ["python", "/opt/desktop/start.py"]
