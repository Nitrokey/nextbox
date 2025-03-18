FROM --platform=linux/aarch64 nextcloud:30.0.1-apache

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update && \
    apt-get -y install --no-install-recommends \
        smbclient
RUN docker-php-ext-install \
    mysqli
