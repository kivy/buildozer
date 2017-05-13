#!/bin/bash

# Mount the disk image
cd /tmp
mkdir /tmp/isomount
mount -t iso9660 /dev/sr1 /tmp/isomount

# Install the drivers
/tmp/isomount/VBoxLinuxAdditions.run

# Cleanup
umount isomount
