# Nitrokey Nextbox (WIP)

This repository contains anything needed to build a Nitrokey Nextbox Appliance 
ready to be flashed on an SD-card for the Raspberry PI4.

## How to create a NextBox image

* Build and flash the raw image using the signed model-assertion
* Boot into the system and register your account
* Customize the initialized image   


### Building and flashing the raw image

Make sure you have the docker daemon running and your current user has permissions to interact
with the daemon. To build the flashable image run:
```bash
$ make
```
The image (`nextbox.img`) will be created in the same directory. 

Assuming your SD-Card is `/dev/sdc` simply run:
```bash
$ dd if=nextbox.img of=/dev/sdc
```

**ATTENTION:** double check that this is the correct device you write to, or you might
end up writing on your system's harddisk.

### Booting into the system

After flashing the SD-card, plug it into the Raspberry PI4, connect a display, keyboard and power
supply to boot the device up. You will be asked for the network configuration (Nitrokey devices 
are configured for LAN and DHCP) and a snapcraft account.

The NextBox bought at Nitrokey will have it set to "snapcraft@nitrokey.com", this represents the
stock configuration. You are free to use your own Snapcraft account here.

The key-pair registered at Snapcraft for the provided account can be used to login via ssh into 
the NextBox.

### Customize the initialized image

Once the image is initialized, make sure you know the IP of the device (e.g., 192.168.123.55).

This repository contains `custom/init_ssh_nextbox.sh`, which will do the remaining configuration
via ssh on the Nextbox. To be able to connect via ssh, the `init_ssh_nextbox.sh` script needs
a `secrets/` directory, which shall contain the private key (filename: `nk_id_rsa`) for the 
registered account. 

Example initialization invokation:
```bash
cd custom
./init_ssh_nextbox.sh ../secrets/ nitrokey-snapcraft@192.168.123.55
```
This assumes that the private key is inside `../secrets` and the Snapcraft user-id is 
`nitrokey-snapcraft` with the device being reachable as `192.168.123.55`. 

The resulting image after this process is the one, which is shipped with the Nitrokey NextBox product.




