Next(Q)EMUBox
=============

* make sure you have `qemu-aarch64-static` available on your system
  * on debian something like: `apt-get install qemu`

* run `bash build_image.sh`
	* creates a 20GB 'harddrive' as file
	* pulls all necessary files from tha internet 
	* qemu will be started and the installation begins

* at some points you'll have to interact with the installation

* you will end up with the image: `disk.qcow2`, which is a complete arm64 debian system

* now we need to extract the kernel and the initrd image to directly pass them to qemu

* run `bash extract-kernel-initrd.sh` and ensure that you have `nbd` installed (deb: nbd-client)

* you should now find `initrd.img-*-arm64` and `vmlinuz-*-arm64` in your working directory

* take a look into `start-nextemubox.sh` and adapt the `KERNEL_IMG` and `INITRD_IMG` version(s) 
	accordingly

* start using `$ bash start-nextemubox.sh` 


**What's missing from here to get a horde of Next(Q)EmuBoxes ?**
* Networking configuration (also for more than one running)
* The image is *only* a debian image, w/o all the quirks and stuff, which are part of `pi-gen`
* Clarify if this really brings any benefits compared to a Debian x86 VirtualBox 

