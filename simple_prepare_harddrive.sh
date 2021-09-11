#!/bin/bash

for cmd in bash sudo parted mkfs.ext4 mkdir mount chown umount chmod; do
	if !(which $cmd > /dev/null); then
		echo "FAIL: missing command: '$cmd'"
		exit;
	fi
done

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

if (mount | grep $dev > /dev/null); then
	echo "found $dev mounted partitions, please unmount them first" 
	exit 1
fi

echo "creating harddisk partition"

# create harddisk partition
sudo parted -ms ${dev} mktable gpt mkpart "NextBoxHardDisk" 1MiB 100%
#sfdisk ${dev} --delete
#echo 'label: gpt' | sfdisk ${dev}
#echo '-;-;linux' | sfdisk ${dev}

sleep 5

echo "creating ext4 partition"

# create ext4 filesystem with label
sudo mkfs.ext4 -F -L NextBoxHardDisk ${dev}1


echo "mounting partition in to 'tmp'"
# mount & chmod 775
sudo mkdir -p tmp
sudo mount ${dev}1 tmp

echo "creating nextbox directory"
sudo mkdir -p tmp/nextbox

echo "create nextcloud, mariadb, apache2 directories"
# ensure custom_apps has the correct owner
sudo mkdir -p tmp/nextcloud/custom_apps
sudo chown 33.0 tmp/nextcloud/custom_apps

# mariadb
sudo mkdir -p tmp/mariadb

# apache config dir (from inside the nextcloud docker)
sudo mkdir -p tmp/apache2

echo "create system log and cache directory"
# also add "journal" to ensure persistance
sudo mkdir -p tmp/varlog/journal
# /var/cache
sudo mkdir -p tmp/varcache

sudo chmod 775 tmp

sleep 5

echo "unmounting partition"
sudo umount tmp

echo "##################################################################"
echo "## To finalize the hard-disk preparation, follow these steps:"
echo "## - mount the 1st partition from your new hard-disk"
echo "## - copy your 'nextbox.conf' to the /nextbox directory"
echo "## - unmount the partition, your hard-disk is now ready to be used"
echo "##################################################################"







