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

if [[ "$dev" = "/dev/sda" ]]; then 
	echo "will not write to /dev/sda, too risky..."
	exit 1	
fi 


# create harddisk partition
parted -ms ${dev} mktable gpt mkpart "NextBoxHardDisk" 1MiB 100%
#sfdisk ${dev} --delete
#echo 'label: gpt' | sfdisk ${dev}
#echo '-;-;linux' | sfdisk ${dev}

echo "waiting 5 secs"
sleep 5

# create ext4 filesystem with label
mkfs.ext4 -F -L NextBoxHardDisk ${dev}1

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

sleep 5

umount tmp



