#!/bin/bash

# setup nbd and mount qemu-disk-image to 'tmp'
sudo modprobe nbd max_part=8
sudo qemu-nbd --connect=/dev/nbd0 disk.qcow2
mkdir tmp
sudo mount /dev/nbd0p1 tmp

# copy whatever kernel + initrd is there
cp tmp/initrd.img-*-arm64 tmp/vmlinuz-*-arm64 .

# cleanup
sync
sudo umount /dev/nbd0p1
sudo nbd-client -d /dev/nbd0

