VERSION=0.2.4
KEY_FILE=../secrets/certs/nextbox.key
TAR_FILE=nextbox-$(VERSION).tar.gz

all:
	echo "no default, try:"
	echo "make release"
 

dev-env:
	make -C nextbox composer
	make -C nextbox dev-setup

release:
	python update_versions.py
	make -C nextbox build-js-production
	tar czf $(TAR_FILE) --exclude=nextbox/node_modules --exclude=nextbox/vendor --exclude=nextbox/build nextbox
	openssl dgst -sha512 -sign $(KEY_FILE) $(TAR_FILE) | openssl base64 > $(TAR_FILE).sig

