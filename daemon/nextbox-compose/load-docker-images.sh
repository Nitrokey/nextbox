#!/bin/bash

if [ ! -f "/usr/lib/nextbox-compose/IMPORTED" ]; then

	docker image load -i /usr/lib/nextbox-compose/docker-images.tar
	touch /usr/lib/nextbox-compose/IMPORTED
	echo "Importing NextBox Docker-Compose Images successful"
else
	echo "NextBox Docker-Compose Images already imported - skipping..."
fi

exit 0
