#!/bin/bash

DEBIAN_VERSION=10.9

# get installation kernel + initrd
baseurl=http://ftp.debian.org/debian/dists/Debian
wget ${baseurl}${DEBIAN_VERSION}/main/installer-arm64/current/images/netboot/debian-installer/arm64/initrd.gz
wget ${baseurl}${DEBIAN_VERSION}/main/installer-arm64/current/images/netboot/debian-installer/arm64/linux

# create image (if missing, else abort)
if [[ -e disk.qcow2 ]]; then
	echo "image: disk.qcow2 already exists, move it away or delete it"
	echo "then restart this script..."
	exit 1
fi

qemu-img create -f qcow2 disk.qcow2 20G

# start qemu and installation
qemu-system-aarch64 -smp 2 -M virt -cpu cortex-a57 -m 1G \
    -initrd initrd.gz \
    -kernel linux -append "root=/dev/ram console=ttyAMA0" \
    -global virtio-blk-device.scsi=off \
    -device virtio-scsi-device,id=scsi \
    -drive file=disk.qcow2,id=rootimg,cache=unsafe,if=none \
    -device scsi-hd,drive=rootimg \
    -netdev user,id=unet -device virtio-net-device,netdev=unet \
    -net user \
    -nographic

