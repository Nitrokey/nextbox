#!/bin/bash

KERNEL_IMG=vmlinuz-4.19.0-16-arm64
INITRD_IMG=initrd.img-4.19.0-16-arm64

# @TODO: network configurations to be as representative as possible
#        -> IPv4 only
#        -> IPv4 + IPv6 
#        -> IPv4 + IPv6 with IPv4 only outgoing (DS-Lite)
#        -> (IPv6 only) maybe not
#
#
# start qemu with kernel, initrd and created image
qemu-system-aarch64 -smp 2 -M virt -cpu cortex-a57 -m 1G \
    -initrd $INITRD_IMG \
    -kernel $KERNEL_IMG \
    -append "root=/dev/sda2 console=ttyAMA0" \
    -global virtio-blk-device.scsi=off \
    -device virtio-scsi-device,id=scsi \
    -drive file=disk.qcow2,id=rootimg,cache=unsafe,if=none \
    -device scsi-hd,drive=rootimg \
    -device e1000,netdev=net0 \
    -net nic \
    -netdev user,hostfwd=tcp:127.0.0.1:2222-:22,id=net0 \
    -nographic
