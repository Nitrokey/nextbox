

image:
	git clone https://github.com/RPi-Distro/pi-gen.git gen-image
	cd gen-image && \
		git checkout 041b97464c01ac6453e4aab59dc931220237bc16
	cp -r image-config/config gen-image
	cp -r image-config/stage-nextbox gen-image
	sed -i -e 's/setarch linux32 //g' gen-image/scripts/common
	cd gen-image && \
		./build.sh
	ls -la deploy

