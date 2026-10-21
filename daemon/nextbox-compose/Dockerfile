FROM --platform=linux/aarch64 nextcloud:33.0.10@sha256:15531d894b5267cba3d0e001c3329c70b4e31ca5f4f0ae14c0a8c0cb57b1956d

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update && \
    apt-get -y install --no-install-recommends \
        smbclient
RUN docker-php-ext-install \
    mysqli
