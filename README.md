Nitrokey's NextBox - Your Private Cloud
=======================================

The NextBox consists of different components, which
mostly are maintained in seperate repositories. All
of those are fully Open-Source and are to be found 
here:

* [`/nextbox`](https://github.com/Nitrokey/nextbox) NextBox Monorepository
* `/daemon` - System Backend daemon
* `/app` - Nextcloud Frontend Application
* `/debian` - Debian Packaging 
* [`nextbox-proxy`](https://github.com/Nitrokey/nextbox-proxy) - Backwards-Proxy Registry Server
* [`nextbox-board`](https://github.com/Nitrokey/nextbox-board) - NextBox' Hardware Shield


This repository is the home of the following tools:

* image building toolchain based on `pi-gen` (arm64), 
  currently the build only works reliably if build 
	on an arm64 architecture

* harddrive preparation tooling, which is needed for
  the harddisk, which shall be used as the *internal*
	harddisk for the NextBox

* `nextemubox` contains the toolchain to build and run
  a NextBox from within QEMU. Still a WIP, but a Debian 
	arm64 image can already be built and started with QEMU.
	See the [`README`](https://github.com/Nitrokey/nextbox/tree/master/nextemubox)
	for more details
