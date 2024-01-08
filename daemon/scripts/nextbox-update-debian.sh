#!/bin/bash

#setting locales

locale-gen --purge en_US.UTF-8
echo -e 'LANG="en_US.UTF-8"\nLANGUAGE="en_US:en"\n' > /etc/default/locale
#prerequisites
echo "executing prerequisites" &&

echo "updating..." &&
apt update &&
apt remove apt-listchanges --assume-yes &&
apt -o Dpkg::Options::="--force-confold" -o Dpkg::Options::="--force-confdef" -fuy dist-upgrade

echo "cleanup" &&
apt  clean &&
apt -fuy  autoremove &&


##upgrade itself

echo "configure upgrade" &&

export DEBIAN_FRONTEND=noninteractive &&
export APT_LISTCHANGES_FRONTEND=none &&

echo "executing buster to bullseye" &&
sudo sed -i 's#/debian-security bullseye/updates# bullseye-security#g' /etc/apt/sources.list
sed -i 's:buster/updates:bullseye-security:' /etc/apt/sources.list
sed -i 's:buster/updates:bullseye-security:' /etc/apt/sources.list.d/*.list
sudo sed -i 's/buster/bullseye/g' /etc/apt/sources.list
sudo sed -i 's/buster/bullseye/g' /etc/apt/sources.list.d/*.list
sudo sed -i 's#/debian-security bullseye/updates# bullseye-security#g' /etc/apt/sources.list



echo "upgrade..." &&

apt update &&
apt  -o Dpkg::Options::="--force-confold"  -o Dpkg::Options::="--force-confdef" -fuy upgrade &&
apt  -o Dpkg::Options::="--force-confold"  -o Dpkg::Options::="--force-confdef" -fuy dist-upgrade

echo "cleanup" &&
apt -fuy  autoremove &&


sed -i 's:/usr/lib/dhcpcd5/dhcpcd:/usr/sbin/dhcpcd:' /etc/systemd/system/dhcpcd.service.d/wait.conf


#reboot
systemctl reboot


