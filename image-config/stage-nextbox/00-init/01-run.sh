#!/bin/bash -e

#echo "${TIMEZONE_DEFAULT}" > "${ROOTFS_DIR}/etc/timezone"
#rm "${ROOTFS_DIR}/etc/localtime"

# update unattended upgrade to our version
install -m 644 ../files/50unattended-upgrades "${ROOTFS_DIR}/etc/apt/apt.conf.d/"
install -m 644 ../files/20auto-upgrades "${ROOTFS_DIR}/etc/apt/apt.conf.d/"
install -m 644 ../files/docker-default "${ROOTFS_DIR}/etc/default/docker"
install -m 644 ../files/nextcloud.service "${ROOTFS_DIR}/etc/avahi/services/"
install -m 644 ../files/journald.conf "${ROOTFS_DIR}/etc/systemd/"


on_chroot << EOF

# done by install above, 
systemctl enable unattended-upgrades
dpkg-reconfigure -f noninteractive unattended-upgrades


echo "LABEL=NextBoxHardDisk	/srv			ext4	defaults,noatime	0	2" >> /etc/fstab
echo "/srv/varlog		/var/log		none	defaults,bind		0	0" >> /etc/fstab
echo "/srv/varcache		/var/cache		none	defaults,bind		0	0" >> /etc/fstab

apt-get install -y ddclient

# disable apache2 autostart not installing certbot-apache anymore!
#rm /etc/systemd/system/multi-user.target.wants/apache2.service

# add ppa:nitrokey/nextbox repository
echo "deb http://ppa.launchpad.net/nitrokey/nextbox/ubuntu groovy main" > /etc/apt/sources.list.d/nitrokey-nextbox.list

# add repository key
apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv-keys 19F7C7BFE72D7141

# update and then install nextbox
apt-get -y update
apt-get -y install nextbox

apt-get -y clean

EOF
