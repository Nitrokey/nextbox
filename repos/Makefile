DEV_DEVICE=192.168.10.50
DEV_USER=nextuser
DEV_ROOT_USER=root

update-daemon:
	# stop nextbox-daemon
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- systemctl stop nextbox-daemon

	# remove caches
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- rm -rf /usr/lib/python3/dist-packages/nextbox_daemon/__pycache__
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- rm -rf /usr/lib/python3/dist-packages/nextbox_daemon/api/__pycache__

	# daemon py-sources
	rsync -r --info=progress --exclude='__pycache__/*' --exclude='api/__pycache__/*' daemon/nextbox_daemon \
		$(DEV_ROOT_USER)@$(DEV_DEVICE):/usr/lib/python3/dist-packages/
	
	### sysd-service files
	for x in daemon/services/*; do \
		rsync $${x} $(DEV_ROOT_USER)@$(DEV_DEVICE):/usr/lib/systemd/system/$$(echo $${x} | cut -d "." -f 2-); \
	done 
	
	### restart nextbox-daemon
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- systemctl daemon-reload
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- systemctl start nextbox-daemon

update-app: app/nextbox/src/
	make -C app/nextbox build-js
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- rm -rf /srv/nextcloud/custom_apps/nextbox/js
	rsync -r --info=progress --exclude='node_modules/*' --exclude='vendor/*' app/nextbox/js \
		$(DEV_ROOT_USER)@$(DEV_DEVICE):/usr/lib/nextbox-app/
	rsync -r --info=progress --exclude='node_modules/*' --exclude='vendor/*' app/nextbox/templates \
		$(DEV_ROOT_USER)@$(DEV_DEVICE):/usr/lib/nextbox-app/
	rsync -r --info=progress --exclude='node_modules/*' --exclude='vendor/*' app/nextbox/lib \
		$(DEV_ROOT_USER)@$(DEV_DEVICE):/usr/lib/nextbox-app/
	rsync -r --info=progress --exclude='node_modules/*' --exclude='vendor/*' app/nextbox/appinfo \
		$(DEV_ROOT_USER)@$(DEV_DEVICE):/usr/lib/nextbox-app/
	#ssh root@192.168.10.50 -- chown root.root -R /srv/nextcloud/custom_apps/nextbox

watch-update-app:
	while true; do \
		inotifywait -e MODIFY --fromfile watch-files-app; \
		make update-app; \
	done 
 
watch-update-daemon:
	while true; do \
		inotifywait -e MODIFY `find daemon/ -name "*.py"`; \
		make update-daemon; \
  done




