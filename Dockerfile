FROM debian:latest
RUN apt-get -y -q update 
RUN apt-get -y -q --no-install-recommends install coreutils quilt parted qemu-user-static debootstrap zerofree zip dosfstools libarchive-tools libcap2-bin grep rsync xz-utils file git curl bc qemu-utils kpartx gpg pigz build-essential make git xxd kmod binfmt-support
RUN apt-get -y install --reinstall ca-certificates