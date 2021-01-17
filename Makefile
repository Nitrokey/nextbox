VERSION=0.2.3
KEY_FILE=../secrets/certs/nextbox.key
TAR_FILE=nextbox-$(VERSION).tar.gz

all:
	echo "no default, try:"
	echo "make release"
	echo "make upload"
  
release:
	tar czf $(TAR_FILE) --exclude=nextbox/node_modules --exclude=nextbox/vendor --exclude=nextbox/build nextbox
	openssl dgst -sha512 -sign $(KEY_FILE) $(TAR_FILE) | openssl base64 > $(TAR_FILE).sig

