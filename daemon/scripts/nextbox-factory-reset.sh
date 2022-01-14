#!/bin/bash

systemctl stop nextbox-compose.service

for dir_name in apache2 letsencrypt logdump mariadb nextbox nextcloud
do
	rm -rf "/srv/${dir_name}"
done

reboot

