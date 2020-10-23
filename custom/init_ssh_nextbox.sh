#!/bin/bash

if [[ "$1" == "" || "$2" == "" || "$3" != "" ]]; then
	echo "usage: $0 <secrets-dir> <username@target-hostname>"
	echo
	echo "<secrets-dir> must contain 'nk_id_rsa'"
	echo "<username@target-hostname> e.g. nitrokey-snapcraft@192.168.1.123"
	exit 1
fi


sec_dir=$1
ssh_url=$2

function scpit
{
	scp -i $sec_dir/nk_id_rsa ${1} ${ssh_url}:${2}
}

function sshrun
{
	ssh -i $sec_dir/nk_id_rsa $ssh_url -- "$@"
}

# ssh-copy files
scpit media-nextcloud.mount /tmp
scpit nextbox-daemon.service /tmp
scpit hostname /tmp

# copy files locally (as root)
sshrun sudo mv /tmp/hostname /etc/writable
sshrun sudo mv /tmp/media-nextcloud.mount /etc/systemd/system
sshrun sudo mv /tmp/nextbox-daemon.service /etc/systemd/system

# reload systemd-units
sshrun sudo systemctl daemon-reload

# enable & start media-nextbox + nextbox-daemon
sshrun sudo systemctl enable media-nextcloud.mount
sshrun sudo systemctl enable nextbox-daemon.service 

sshrun sudo systemctl restart media-nextcloud.mount
sshrun sudo systemctl restart nextbox-daemon.service 

# snap connection(s)
sshrun sudo snap connect nextcloud-nextbox:removable-media










