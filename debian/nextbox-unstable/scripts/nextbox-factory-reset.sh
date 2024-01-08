#!/bin/bash

systemctl stop nextbox-compose.service
systemctl stop docker

for dir_name in apache2 letsencrypt logdump mariadb nextbox nextcloud
do
	rm -rf "/srv/${dir_name}"
done

rm -rf "/srv/docker/*"

DEBIAN_FRONTEND=noninteractive
NEEDRESTART_MODE=a

dpkg --configure -a


reboot

