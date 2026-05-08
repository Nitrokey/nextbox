#!/bin/bash

echo "Starting Debian 12 update on $(date -Iseconds)" 2>&1 >> /var/log/nextbox-update-debian.log

#first of all lets kill all docker instances
echo "stopping nextbox compose service" 2>&1 >> /var/log/nextbox-update-debian.log
systemctl stop nextbox-compose.service 2>&1 >> /var/log/nextbox-update-debian.log

#disable package manager interactions
export DEBIAN_FRONTEND=noninteractive 
export APT_LISTCHANGES_FRONTEND=none 

echo "executing system upgrade (pre version upgrade)" >> /var/log/nextbox-update-debian.log

apt update 2>&1 >> /var/log/nextbox-update-debian.log
#apt remove apt-listchanges --assume-yes 
apt -o Dpkg::Options::="--force-confold" -o Dpkg::Options::="--force-confdef" -fuy dist-upgrade 2>&1 >> /var/log/nextbox-update-debian.log

#package cleanup
echo "executing package cleanup (pre version upgrade)" >> /var/log/nextbox-update-debian.log

apt clean 2>&1 >> /var/log/nextbox-update-debian.log
apt -fuy autoremove 2>&1 >> /var/log/nextbox-update-debian.log

#debian version upgrade itself
echo "Patching sources.list from bullseye to bookworn" >> /var/log/nextbox-update-debian.log

# Generic repository version changes
sed -i 's#bullseye-security#bookworm-security#g' /etc/apt/sources.list
sed -i 's#bullseye-updates#bookworm-updates#g' /etc/apt/sources.list
sed -i 's#bullseye#bookworm#g' /etc/apt/sources.list
sed -i 's#bullseye#bookworm#g' /etc/apt/sources.list.d/*.list
# move from non-free to non-free-firmware, as we only use firmware from non-free currently
sed -i 's#non-free#non-free-firmware#g' /etc/apt/sources.list

# Executing the actual version upgrade
echo "executing debian version upgrade..." >> /var/log/nextbox-update-debian.log

apt update 2>&1 >> /var/log/nextbox-update-debian.log
apt  -o Dpkg::Options::="--force-confnew"  -o Dpkg::Options::="--force-confdef" -fuy upgrade 2>&1 >> /var/log/nextbox-update-debian.log
apt  -o Dpkg::Options::="--force-confnew"  -o Dpkg::Options::="--force-confdef" -fuy dist-upgrade 2>&1 >> /var/log/nextbox-update-debian.log

echo "cleanup" >> /var/log/nextbox-update-debian.log

apt -fuy autoremove 2>&1 >> /var/log/nextbox-update-debian.log

# debian deprecated apt-key in favour of individual key files in /etc/apt/trusted.gpg.d/
# this move the nitrokey PPA key there to prevent warnings and possible later errors on full deprection
apt-key export E72D7141 | gpg --dearmour -o /etc/apt/trusted.gpg.d/nitrokey-ppa.gpg

#reboot
echo "upgrade finished: rebooting" >> /var/log/nextbox-update-debian.log
systemctl reboot
