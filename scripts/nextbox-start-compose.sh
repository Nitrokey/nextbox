#!/usr/bin/bash

if (grep '21.0.2' /srv/nextcloud/version.php); then 
	/usr/bin/docker-compose -f docker-compose-badnc.yml up
else 
	/usr/bin/docker-compose -f docker-compose.yml up
fi


