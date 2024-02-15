#!/bin/bash

#first of all lets kill all docker instances
echo "stopping nextbox" >> /var/log/nextbox-update-debian.log
systemctl stop nextbox-compose.service

#setting locales
echo "generating locale" >> /var/log/nextbox-update-debian.log

locale-gen --purge en_US.UTF-8 
echo -e 'LANG="en_US.UTF-8"\nLANGUAGE="en_US:en"\n' > /etc/default/locale

#prerequisites
echo "executing prerequisites" >> /var/log/nextbox-update-debian.log

export DEBIAN_FRONTEND=noninteractive 
export APT_LISTCHANGES_FRONTEND=none 

echo "updating..." >> /var/log/nextbox-update-debian.log

apt update 
apt remove apt-listchanges --assume-yes 
apt -o Dpkg::Options::="--force-confold" -o Dpkg::Options::="--force-confdef" -fuy dist-upgrade

echo "cleanup" >> /var/log/nextbox-update-debian.log

apt  clean 
apt -fuy  autoremove 


##upgrade itself

echo "executing buster to bullseye" >> /var/log/nextbox-update-debian.log

sed -i 's#/debian-security bullseye/updates# bullseye-security#g' /etc/apt/sources.list
sed -i 's:buster/updates:bullseye-security:' /etc/apt/sources.list
sed -i 's:buster/updates:bullseye-security:' /etc/apt/sources.list.d/*.list
sed -i 's/buster/bullseye/g' /etc/apt/sources.list
sed -i 's/buster/bullseye/g' /etc/apt/sources.list.d/*.list
sed -i 's#/debian-security bullseye/updates# bullseye-security#g' /etc/apt/sources.list



echo "upgrade..." >> /var/log/nextbox-update-debian.log

apt update 
apt  -o Dpkg::Options::="--force-confold"  -o Dpkg::Options::="--force-confdef" -fuy upgrade 
apt  -o Dpkg::Options::="--force-confold"  -o Dpkg::Options::="--force-confdef" -fuy dist-upgrade

echo "cleanup" >> /var/log/nextbox-update-debian.log

apt -fuy  autoremove

sed -i 's:/usr/lib/dhcpcd5/dhcpcd:/usr/sbin/dhcpcd:' /etc/systemd/system/dhcpcd.service.d/wait.conf


#reboot
echo "upgrade finished: rebooting" >> /var/log/nextbox-update-debian.log
systemctl reboot


