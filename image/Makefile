

image:
	git clone https://github.com/RPi-Distro/pi-gen.git gen-image
	cd gen-image && \
		git checkout 1a5baa1d3592e42899d7553bdf00a4cabc364564
	cp -r image-config/config gen-image
	cp -r image-config/stage-nextbox gen-image
	sed -i -e 's/setarch linux32 //g' gen-image/scripts/common
	cd gen-image && \
		./build.sh
	find . -name deploy

