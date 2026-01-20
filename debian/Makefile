VERSION=$(shell head -n 1 debian/changelog | grep -Eo '[0-9\.\-]*')

IMAGE_NAME=nextbox-build

#PKG=nextbox
#PKG=nextbox-testing
PKG=nextbox-unstable

GIT_TAG=main


DEB_PKG=$(PKG)_$(VERSION)_all.deb
DEB_SRC=$(PKG)_$(VERSION)_source.changes

unstable:
	rm -rf nextbox-unstable
	rm -f repos/app/nextbox/js/*
	docker run --rm --name $(IMAGE_NAME) -it \
		-v $(HOME)/.gnupg:/root/.gnupg \
		-v $(HOME)/.dput.cf:/root/.dput.cf \
		-v $(shell pwd):/build \
		-v $(shell pwd)/../app:/app \
		-v $(shell pwd)/../daemon:/daemon \
		-v $(shell pwd)/../janitor:/janitor \
		-p 8080:80 \
		$(IMAGE_NAME):stable make PKG=nextbox-unstable GIT_TAG=main main-target

testing:
	rm -rf nextbox-testing
	rm -f repos/app/nextbox/js/*
	docker run --rm --name $(IMAGE_NAME) -it \
		-v $(HOME)/.gnupg:/root/.gnupg \
		-v $(HOME)/.dput.cf:/root/.dput.cf \
		-v $(shell pwd):/build \
		-v $(shell pwd)/../app:/app \
		-v $(shell pwd)/../daemon:/daemon \
		-v $(shell pwd)/../janitor:/janitor \
		-p 8080:80 \
		$(IMAGE_NAME):stable make PKG=nextbox-testing GIT_TAG=main main-target

stable:
	rm -rf nextbox
	rm -f repos/app/nextbox/js/*
	docker run --rm --name $(IMAGE_NAME) -it \
		-v $(HOME)/.gnupg:/root/.gnupg \
		-v $(HOME)/.dput.cf:/root/.dput.cf \
		-v $(shell pwd):/build \
		-v $(shell pwd)/../app:/app \
		-v $(shell pwd)/../daemon:/daemon \
		-v $(shell pwd)/../janitor:/janitor \
		-p 8080:80 \
		$(IMAGE_NAME):stable make PKG=nextbox GIT_TAG=main main-target


clean:
	#rm -rf $(PKG)/app $(PKG)/nextbox_daemon $(PKG)/setup.py $(PKG)/nextbox-compose
	rm -rf nextbox nextbox-testing nextbox-unstable
	make PKG=nextbox-unstable GIT_TAG=main deb-clean
	make PKG=nextbox-testing GIT_TAG=main deb-clean
	make PKG=nextbox GIT_TAG=main deb-clean


main-target: $(PKG)/janitor $(PKG)/app $(PKG)/nextbox_daemon $(PKG)/scripts $(PKG)/templates $(PKG)/nextbox-compose $(PKG)/debian $(PKG)/rtun-linux-arm64 deb-src


$(PKG)/debian: debian
	rsync -r debian $(PKG)
	sed -i -e 's/%%PKG%%/$(PKG)/g' $(PKG)/debian/control
	sed -i -e 's/%%PKG%%/$(PKG)/g' $(PKG)/debian/changelog
	cp repos/daemon/services/nextbox.nextbox-daemon.service $(PKG)/debian/$(PKG).nextbox-daemon.service
	cp repos/daemon/services/nextbox.nextbox-compose.service $(PKG)/debian/$(PKG).nextbox-compose.service
	cp repos/daemon/services/nextbox.nextbox-image-load.service $(PKG)/debian/$(PKG).nextbox-image-load.service
	cp repos/daemon/services/nextbox.reverse-tunnel.service $(PKG)/debian/$(PKG).reverse-tunnel.service
	cp repos/daemon/services/nextbox.nextbox-factory-reset.service $(PKG)/debian/$(PKG).nextbox-factory-reset.service
	cp repos/daemon/services/nextbox.nextbox-updater.service $(PKG)/debian/$(PKG).nextbox-updater.service
	cp janitor/nextbox_status_page.service $(PKG)/debian/$(PKG).nextbox_status_page.service

$(PKG)/app: repos/app/nextbox/js/nextbox-main.js
	mkdir -p $(PKG)/app/nextbox
	
	rsync -r repos/app/nextbox/lib $(PKG)/app/nextbox
	rsync -r repos/app/nextbox/img $(PKG)/app/nextbox
	rsync -r repos/app/nextbox/js $(PKG)/app/nextbox
	rsync -r repos/app/nextbox/css $(PKG)/app/nextbox
	rsync -r repos/app/nextbox/templates $(PKG)/app/nextbox
	rsync -r repos/app/nextbox/appinfo $(PKG)/app/nextbox

repos/app/nextbox/package-lock.json:
	make -C /build/repos/app/nextbox npm-install

repos/app/nextbox/js/nextbox-main.js: repos/app/nextbox/package-lock.json
	make -C /build/repos/app/nextbox build-js-production

$(PKG)/nextbox-compose:
	# nextbox-compose
	rsync -r repos/daemon/nextbox-compose $(PKG)

$(PKG)/nextbox_daemon: $(PKG)/debian
	mkdir -p $(PKG)/nextbox_daemon 
	
	# daemon itself
	rsync -r repos/daemon/nextbox_daemon $(PKG)
	cp repos/daemon/setup.py $(PKG)/

$(PKG)/scripts: repos/daemon/scripts $(PKG)/debian
	mkdir -p $(PKG)/scripts
	cp repos/daemon/scripts/* $(PKG)/scripts

$(PKG)/templates: repos/daemon/templates $(PKG)/debian
	mkdir -p $(PKG)/templates
	cp repos/daemon/templates/* $(PKG)/templates


$(PKG)/janitor: repos/janitor $(PKG)/debian
	mkdir -p $(PKG)/janitor
	cp repos/janitor/* $(PKG)/janitor

$(PKG)/rtun-linux-arm64: $(PKG)/debian
	cd $(PKG) && \
		wget https://github.com/snsinfu/reverse-tunnel/releases/download/v1.3.0/rtun-linux-arm64


###
### debian docker
###

start-dev-docker: dev-image
	-docker stop $(IMAGE_NAME)
	-docker rm $(IMAGE_NAME)
	sleep 5
	docker run --rm --name $(IMAGE_NAME) -d -it \
		-v $(HOME)/.gnupg:/root/.gnupg \
		-v $(HOME)/.dput.cf:/root/.dput.cf \
		-v $(shell pwd):/build \
		-v $(shell pwd)/../app:/app \
		-v $(shell pwd)/../daemon:/daemon \
		-v $(shell pwd)/../janitor:/janitor \
		-p 8080:80 \
		$(IMAGE_NAME):stable
	
enter-dev-docker: start-dev-docker
	docker exec -it $(IMAGE_NAME) bash

dev-image: Dockerfile
	docker build --label $(IMAGE_NAME) --tag $(IMAGE_NAME):stable --network host .
	touch $@

###
### build source package
###

$(DEB_SRC): $(PKG)/janitor $(PKG)/app $(PKG)/nextbox_daemon $(PKG)/nextbox-compose $(PKG)/debian
	cd $(PKG) && \
		dpkg-buildpackage -S
	#debsign -k CBF5C9FD2105C32B1E9CDC2C0303797FE98B51CD nextbox_$(VERSION)_source.changes

$(DEB_PKG): $(DEB_SRC) $(PKG)/app/nextbox/js/nextbox-main.js $(PKG)/nextbox_daemon $(PKG)/debian/control $(PKG)/debian/rules $(PKG)/debian/dirs $(PKG)/debian/install $(PKG)/debian/source/options
	# -us -uc for non signed build
	cd $(PKG) && \
		fakeroot dpkg-buildpackage -b 

deb-clean:
	rm -f $(PKG)_$(VERSION)_all.*
	rm -f $(PKG)_$(VERSION)_arm64.*
	rm -f $(PKG)_$(VERSION)_amd64.*
	rm -f $(PKG)_$(VERSION)_source.*
	rm -f $(PKG)_$(VERSION).dsc
	rm -f $(PKG)_$(VERSION).tar.gz

deb-src: $(PKG)/janitor $(PKG)/app $(PKG)/nextbox_daemon $(PKG)/nextbox-compose $(PKG)/debian
	make PKG=$(PKG) GIT_TAG=$(GIT_TAG) $(DEB_SRC)
	make PKG=$(PKG) GIT_TAG=$(GIT_TAG) upload

deb:
	make PKG=$(PKG) GIT_TAG=$(GIT_TAG) $(DEB_PKG)

upload:
	dput nextbox $(DEB_SRC)


.PHONY: deb deb-src upload stable main-target unstable testing stable

