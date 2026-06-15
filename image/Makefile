.PHONY: ensure-checkout build-image clean clean-docker

COMMIT_HASH := 67262a4ad0959aab2a9d84a6392b1967999e8f50

gen-image:
	git clone https://github.com/RPi-Distro/pi-gen.git gen-image

ensure-checkout: gen-image
	git -C gen-image fetch --all
	git -C gen-image reset --hard $(COMMIT_HASH)
	git -C gen-image clean -fdx
	git -C gen-image apply ../gen-image_export-image.patch

build-image: ensure-checkout
	cp -r image-config/config gen-image
	cp -r image-config/stage-nextbox gen-image
	cd gen-image && ./build.sh
	#find . -name deploy

build-image-docker: ensure-checkout
	cp -r image-config/config gen-image
	cp -r image-config/stage-nextbox gen-image
	cd gen-image && CONTINUE=1 ./build-docker.sh
	#find . -name deploy

clean:
	rm -rf gen-image

clean-docker: clean
	docker container rm -v pigen_work
