FROM debian:buster

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV container docker
ENV PATH "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin"
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8


RUN apt-get update && apt-get install -y dh-python python3-setuptools python3-all dh-systemd \
	python3 python3-flask python3-flask python3-gpiozero python3-yaml python3-psutil \
	debhelper build-essential python3-requests docker-compose docker.io vim npm \
	software-properties-common dput devscripts gnupg dh-make lintian \
	php phpunit rsync wget

RUN add-apt-repository -y ppa:nitrokey/nextbox

WORKDIR "/build"
