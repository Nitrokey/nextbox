FROM --platform=linux/aarch64 nextcloud:33.0.11-apache@sha256:514adc7768440c3331482a11665e590448916efce77716224dc288d5a4b1cbb1

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update && \
    apt-get -y install --no-install-recommends \
        smbclient
RUN docker-php-ext-install \
    mysqli
# Temporarily disble opcache.jit, as upstream fix seems to be delayed > https://github.com/nextcloud/docker/issues/2576
RUN echo 'opcache.jit=disable' >> /usr/local/etc/php/conf.d/opcache-recommended.ini
