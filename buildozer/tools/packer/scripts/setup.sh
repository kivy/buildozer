#!/bin/bash
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus"

# ensure the kivy user can mount shared folders
adduser kivy vboxsf

# create a space specifically for builds
mkdir /build
chown kivy /build

# add a little face
wget $PACKER_HTTP_ADDR/kivy-icon-96.png
mv kivy-icon-96.png /home/kivy/.face
chown kivy.kivy /home/kivy/.face

# set wallpaper
wget $PACKER_HTTP_ADDR/wallpaper.png
mv wallpaper.png /usr/share/backgrounds/kivy-wallpaper.png
xfconf-query -c xfce4-desktop \
    --property /backdrop/screen0/monitor0/workspace0/last-image \
    --set /usr/share/backgrounds/kivy-wallpaper.png

# change theme (works better for this wallpaper)
xfconf-query -c xsettings \
    --property /Net/ThemeName \
    --set Adwaita
xfconf-query -c xsettings \
    --property /Net/IconThemeName \
    --set elementary-xfce-darker

# copy welcome directory
mkdir -p /usr/share/applications/buildozer-welcome
cd /usr/share/applications/buildozer-welcome
wget $PACKER_HTTP_ADDR/welcome/milligram.min.css
wget $PACKER_HTTP_ADDR/welcome/buildozer.css
wget $PACKER_HTTP_ADDR/welcome/index.css
cd -
