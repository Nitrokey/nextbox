#!/bin/bash
set -eo pipefail
exec >> /var/log/nextbox-update-debian.log 2>&1
trap 'echo "===== ERROR in line $LINENO: $BASH_COMMAND ====="' ERR

echo "===== Starting Debian 12 update on $(date -Iseconds) ====="

#first of all lets kill all docker instances
echo "===== stopping nextbox compose service ====="
systemctl stop nextbox-compose.service

#disable package manager interactions
export DEBIAN_FRONTEND=noninteractive
export APT_LISTCHANGES_FRONTEND=none
export NEEDRESTART_SUSPEND=1

# retry network dependent apt-get calls, recovering an interrupted dpkg state between attempts
# 5 minute waits in between attempts
apt_retry() {
    local i
    for i in 1 2 3; do
        apt-get -o Acquire::Retries=3 "$@" && return 0
        echo "===== attempt $i failed: apt-get $* ====="
        sleep 300
        dpkg --force-confnew --configure -a || true
    done
    return 1
}

# debian deprecated apt-key in favour of individual key files in /etc/apt/trusted.gpg.d/
# this move the nitrokey PPA key there to prevent warnings and possible later errors on full deprection
NITROKEY_GPG=/etc/apt/trusted.gpg.d/nitrokey-ppa.gpg
if [ ! -s "$NITROKEY_GPG" ]; then
    key=$(apt-key export E72D7141 2>/dev/null) || true
    if [ -n "$key" ]; then
        gpg --dearmour --yes -o "$NITROKEY_GPG" <<< "$key"
        apt-key --keyring /etc/apt/trusted.gpg del E72D7141 || true
    fi
fi

# skipped on re-runs once the sources point to bookworm
if grep -qw bullseye /etc/apt/sources.list; then
    echo "===== executing system upgrade (pre version upgrade) ====="

    #Fixup possible inconsistent prior updates
    dpkg --force-confdef --force-confold --configure -a || true

    # Update first. Error on network error. Prevent failure when ord repositories
    apt-get update || true
    apt-get -o Dpkg::Options::="--force-confold" -o Dpkg::Options::="--force-confdef" -fuy dist-upgrade || true

    #package cleanup
    echo "===== executing package cleanup (pre version upgrade) ====="

    apt-get clean || true
    apt-get -fuy autoremove || true
fi

#debian version upgrade itself
echo "===== Patching sources.list from bullseye to bookworm ====="

# Generic repository version changes
sed -i 's#bullseye-security#bookworm-security#g' /etc/apt/sources.list
sed -i 's#bullseye-updates#bookworm-updates#g' /etc/apt/sources.list
sed -i 's#bullseye#bookworm#g' /etc/apt/sources.list
for f in /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources; do
    if [ -e "$f" ]; then sed -i 's#bullseye#bookworm#g' "$f"; fi
done
# move from non-free to non-free-firmware, as we only use firmware from non-free currently
sed -i -E 's#non-free( |$)#non-free-firmware\1#g' /etc/apt/sources.list
# Fix: remove possible old snapshot repos used for old debian11 images
if grep -qs 'snapshot\.debian\.org' /etc/apt/sources.list; then
    sed -i -E \
        's#^deb (\[[^]]*\] )?https?://snapshot\.debian\.org/archive/([^/]+)/[^ ]+#deb http://deb.debian.org/\2#' \
        /etc/apt/sources.list
fi

# Executing the actual version upgrade
echo "===== executing debian version upgrade... ====="

export UCF_FORCE_CONFFNEW=1
dpkg --force-confnew --configure -a || true
apt_retry -o APT::Update::Error-Mode=any update
# update dpkg first, as bullseye's dpkg can't unpack zstd compressed packages, used by the raspberry pi repo
apt_retry -o Dpkg::Options::="--force-confnew" -fuy install dpkg
apt_retry -o Dpkg::Options::="--force-confnew" -fuy upgrade
apt_retry -o Dpkg::Options::="--force-confnew" -fuy dist-upgrade

echo "===== kernel and boot partition update ====="

# Move the boot partition to /boot/firmware
if mountpoint -q /boot; then umount /boot; fi
if ! mountpoint -q /boot/firmware && [ -n "$(ls -A /boot/firmware 2>/dev/null)" ]; then
    mv /boot/firmware "/boot/firmware.rootfs-old-$(date +%s)"
fi
mkdir -p /boot/firmware
sed -E -i 's|^([^#[:space:]]+[[:space:]]+)/boot([[:space:]])|\1/boot/firmware\2|' /etc/fstab
systemctl daemon-reload
if ! mountpoint -q /boot/firmware; then mount /boot/firmware; fi
mountpoint -q /boot/firmware

# Add new firmware and kernel
apt_retry install -y --reinstall raspi-firmware
apt_retry install -y linux-image-rpi-v8 linux-headers-rpi-v8
# Purge old kernel as last step
apt-get purge -y raspberrypi-kernel || true

echo "===== cleanup ====="

apt-get -fuy autoremove || true

# Add systemd-resolved, which is required after debian 12 upadte
# this depency can currently not be accounted for with the current package architecture
# this will be fixed when the systems are on debian 12
# installed last, as it can break DNS resolution until reboot
apt_retry -o Dpkg::Options::="--force-confnew" -fuy install systemd-resolved

#reboot
echo "===== upgrade finished: rebooting ====="
systemctl reboot
