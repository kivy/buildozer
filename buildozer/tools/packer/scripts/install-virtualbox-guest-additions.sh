#!/bin/bash

# Mount the disk image
cd /tmp
mkdir /tmp/isomount
mount -t iso9660 -o loop /root/VBoxGuestAdditions.iso /tmp/isomount

# Install the drivers
/tmp/isomount/VBoxLinuxAdditions.run

# Cleanup
umount isomount
rm -rf isomount /root/VBoxGuestAdditions.iso
