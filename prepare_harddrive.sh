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

if [[ ! -a "$dev" ]]; then
	echo "device: $dev does not exist, exiting..."
	exit 1
fi


# create harddisk partition
sfdisk ${dev} --delete
echo 'label: gpt' | sfdisk ${dev}
echo '-;-;linux' | sfdisk ${dev}

# create ext4 filesystem with label
mkfs.ext4 -L NextBoxHardDisk ${dev}1

# mount & chmod 775
mkdir -p tmp
mount ${dev}1 tmp
mkdir -p tmp/nextbox

# ensure custom_apps has the correct owner
mkdir -p tmp/nextcloud/custom_apps
chown 33.0 tmp/nextcloud/custom_apps

mkdir -p tmp/mariadb

# also add "journal" to ensure persistance
mkdir -p tmp/varlog/journal

# apache config dir (from inside the nextcloud docker)
mkdir -p tmp/apache2

# /var/cache
mkdir -p tmp/varcache

chmod 775 tmp

umount tmp



