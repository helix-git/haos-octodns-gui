ARG BUILD_FROM
# hadolint ignore=DL3006
FROM $BUILD_FROM

# Install requirements (git needed for octodns-pihole)
# hadolint ignore=DL3018
RUN \
    apk add --no-cache \
        bash \
        python3 \
        py3-pip \
        py3-yaml \
        gcc \
        musl-dev \
        python3-dev \
        libffi-dev \
        git

# Install OctoDNS Core + all providers
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --break-system-packages \
    octodns>=1.0 \
    octodns-cloudflare \
    octodns-ovh \
    octodns-netbox-dns \
    octodns-netbox \
    octodns-bind \
    "git+https://github.com/jvoss/octodns-pihole.git"

# Copy app directory
COPY app /app/
COPY run.sh /

RUN pip install --no-cache-dir -r /app/requirements.txt --break-system-packages \
    && chmod a+x /run.sh

CMD [ "/run.sh" ]
