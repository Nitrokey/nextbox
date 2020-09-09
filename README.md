# Nitrokey Nextbox (WIP)

This repository contains anything needed to build a Nitrokey Nextbox Appliance 
ready to be flashed on an SD-card for the Raspberry PI4.

Make sure you have the docker daemon running and your current user has permissions to interact
with the daemon. To build the flashable image run:
```bash
$ make
```
Assuming your SD-Card is `/dev/sdc` simply run:
```bash
$ dd if=nextbox.img of=/dev/sdc
```

**ATTENTION:** double check that this is the correct device you write to, or you might
end up writing on your system's harddisk.


The image (`nextbox.img`) will be created in the same directory. 
This approach will use the checked-in, signed model-assertion, which can also be 
created using this repository:

* special docker image has to be prepared / build
* snap(s) placed inside the image must be available on snapcraft (in stable state)
* cryptographic key (for signing) has to be created and registered at snap(craft)
* a model assertion has to be created and signed
* the signed model assertion can be used to build the appliance




