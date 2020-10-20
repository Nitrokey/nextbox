#!/bin/bash

uid=$(id -u)

if [[ "$uid" != "0" ]]; then
	echo "need root!"
	exit 1
fi

if [[ "$1" = "" || "$2" != "" ]]; then
	echo "usage: $0 <disk-device>"
	exit 1
fi

dev=$1


# create harddisk partition
sfdisk ${dev} --delete
echo 'label: gpt' | sfdisk ${dev}
echo '-;-;linux' | sfdisk ${dev}

# create ext4 filesystem with label
mkfs.ext4 -L NextBoxHardDisk ${dev}1

# mount & chmod 775
mkdir -p tmp
mount ${dev}1 tmp
chmod 775 tmp
umount tmp



