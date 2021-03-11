DEV_DEVICE=192.168.10.50
DEV_USER=nextuser
DEV_ROOT_USER=root

update-daemon:
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- systemctl stop nextbox-daemon
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- rm -rf /usr/lib/python3/dist-packages/nextbox_daemon/__pycache__
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- rm -rf /usr/lib/python3/dist-packages/nextbox_daemon/api/__pycache__
	rsync -r --info=progress --exclude='__pycache__/*' --exclude='api/__pycache__/*' src/nextbox_daemon \
		$(DEV_ROOT_USER)@$(DEV_DEVICE):/usr/lib/python3/dist-packages/
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- systemctl start nextbox-daemon

update-app: src/app/nextbox/src/
	make -C src dev
	ssh $(DEV_ROOT_USER)@$(DEV_DEVICE) -- rm -rf /srv/nextcloud/custom_apps/nextbox/js
	rsync -r --info=progress --exclude='node_modules/*' --exclude='vendor/*' src/app/nextbox/js \
		$(DEV_ROOT_USER)@$(DEV_DEVICE):/usr/lib/nextbox-app/
	rsync -r --info=progress --exclude='node_modules/*' --exclude='vendor/*' src/app/nextbox/lib/Controller \
		$(DEV_ROOT_USER)@$(DEV_DEVICE):/usr/lib/nextbox-app/
	#ssh root@192.168.10.50 -- chown root.root -R /srv/nextcloud/custom_apps/nextbox

watch-update-app:
	while true; do \
		inotifywait -e MODIFY --fromfile watch-files-app; \
		make update-app; \
	done 
 
watch-update-daemon:
	while true; do \
		inotifywait -e MODIFY `find src/nextbox_daemon/ -name "*.py"`; \
		make update-daemon; \
  done




