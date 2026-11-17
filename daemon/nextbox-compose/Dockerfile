FROM --platform=linux/aarch64 nextcloud:33.0.11@sha256:504714d8dac82e8ceabd0cd9ede179a92b0db3a5ae4f85e26ec13e8d36ac7739

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update && \
    apt-get -y install --no-install-recommends \
        smbclient
RUN docker-php-ext-install \
    mysqli
# Temporarily disble opcache.jit, as upstream fix seems to be delayed > https://github.com/nextcloud/docker/issues/2576
RUN echo 'opcache.jit=disable' >> /usr/local/etc/php/conf.d/opcache-recommended.ini
