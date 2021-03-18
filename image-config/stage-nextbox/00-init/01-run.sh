#!/bin/bash -e


#### what default timezone should we set ???
#echo "${TIMEZONE_DEFAULT}" > "${ROOTFS_DIR}/etc/timezone"
#rm "${ROOTFS_DIR}/etc/localtime"

# modify /boot/cmdline.txt (kernel-cmdline) to use quirks (no UAS, strict usb-storage) for SATA-USB adapter
sed -i -e 's/rootwait quiet/usb-storage.quirks=0x152d:0x1561:u rootwait quiet/g' "${ROOTFS_DIR}/boot/cmdline.txt"
# [x] 152d:1561 => 'Sabrent' adapter using 'JMicron Chipset'
# [ ] 174c:55aa => 'SKL' & 'Inateck' adapters using 'ASMedia Chipset'


# unattended upgrades configuration (1st apt.conf 'always' allow run, based on systemd-timers)
install -m 644 ../files/50unattended-upgrades "${ROOTFS_DIR}/etc/apt/apt.conf.d/"
install -m 644 ../files/20auto-upgrades "${ROOTFS_DIR}/etc/apt/apt.conf.d/"

mkdir -p /etc/systemd/system/apt-daily.timer.d
install -m 644 ../files/override.apt-daily.timer.conf \
	"${ROOTFS_DIR}/etc/systemd/system/apt-daily.timer.d/override.conf"

mkdir -p /etc/systemd/system/apt-daily-upgrade.timer.d
install -m 644 ../files/override.apt-daily-upgrade.timer.conf \
	"${ROOTFS_DIR}/etc/systemd/system/apt-daily-upgrade.timer.d/override.conf"

# docker default configuration, change docker lib-dir to /srv/docker
install -m 644 ../files/docker-default "${ROOTFS_DIR}/etc/default/docker"

# avahi-daemon service to promote NextCloud as http-service using "nextbox.local"
install -m 644 ../files/nextcloud.service "${ROOTFS_DIR}/etc/avahi/services/"

# journald-config to keep size limited
install -m 644 ../files/journald.conf "${ROOTFS_DIR}/etc/systemd/"

# sudo -> nextuser can sudo without a password
install -m 440 ../files/01_nextuser-nopasswd "${ROOTFS_DIR}/etc/sudoers.d/"

# docker images for 1st boot
mkdir -p "${ROOTFS_DIR}/usr/lib/nextbox-compose/"
install -m 644 ../files/docker-images.tar "${ROOTFS_DIR}/usr/lib/nextbox-compose/"

on_chroot << EOF

# done by install above, (isn't this bad and overwrites stuff we set before ???)
systemctl enable unattended-upgrades
dpkg-reconfigure -f noninteractive unattended-upgrades


echo "LABEL=NextBoxHardDisk	/srv			ext4	defaults,noatime	0	2" >> /etc/fstab
echo "/srv/varlog		/var/log		none	defaults,bind		0	0" >> /etc/fstab
echo "/srv/varcache		/var/cache		none	defaults,bind		0	0" >> /etc/fstab

apt-get install -y ddclient

# add ppa:nitrokey/nextbox repository
echo "deb http://ppa.launchpad.net/nitrokey/nextbox/ubuntu groovy main" > /etc/apt/sources.list.d/nitrokey-nextbox.list

# add repository key
apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv-keys 19F7C7BFE72D7141

# update and then install nextbox
apt-get -y update
apt-get -y install nextbox

apt-get -y clean

EOF
