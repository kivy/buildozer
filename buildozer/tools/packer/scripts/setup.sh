#!/bin/bash
# xfconf doesn't work with sudo, even with XAUTHORITY + DISPLAY
# seems that the user need to log to be able to use them.

# keep them for reference for now.
# change theme (works better for this wallpaper)
# xfconf-query -c xfce4-desktop \
#     --property /backdrop/screen0/monitor0/workspace0/last-image \
#     --set /usr/share/backgrounds/kivy-wallpaper.png
# xfconf-query -c xsettings \
#     --property /Net/ThemeName \
#     --set Adwaita
# xfconf-query -c xsettings \
#     --property /Net/IconThemeName \
#     --set elementary-xfce-darker



set -x

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
sed -i "s:/usr/share/xfce4/backdrops/xubuntu-wallpaper.png:/usr/share/backgrounds/kivy-wallpaper.png:g" /etc/xdg/xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml
sed -i "s:Greybird:Adwaita:g" /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml
sed -i "s:Greybird:Adwaita:g" /etc/xdg/xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml
sed -i "s:Greybird:Adwaita:g" /etc/xdg/xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml
sed -i "s:Greybird:Adwaita:g" /etc/xdg/xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/xfce4-notifyd.xml
sed -i "s:elementary-xfce-darker:elementary-xfce-darkest:g" /etc/xdg/xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml
sed -i "s:elementary-xfce-dark:elementary-xfce-darkest:g" /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml

# add desktop icon
wget $PACKER_HTTP_ADDR/buildozer.desktop
mkdir -p /home/kivy/Desktop
cp buildozer.desktop /home/kivy/Desktop/
chown kivy.kivy -R /home/kivy/Desktop
chmod +x /home/kivy/Desktop/buildozer.desktop
mv buildozer.desktop /usr/share/applications/
sed -i "s:^favorites=.*$:favorites=buildozer.desktop,exo-terminal-emulator.desktop,exo-web-browser.desktop,xfce-keyboard-settings.desktop,exo-file-manager.desktop,org.gnome.Software.desktop,xfhelp4.desktop:g" /etc/xdg/xdg-xubuntu/xfce4/whiskermenu/defaults.rc

# copy welcome directory
mkdir -p /usr/share/applications/buildozer-welcome
cd /usr/share/applications/buildozer-welcome
wget $PACKER_HTTP_ADDR/welcome/milligram.min.css
wget $PACKER_HTTP_ADDR/welcome/buildozer.css
wget $PACKER_HTTP_ADDR/welcome/index.html
wget $PACKER_HTTP_ADDR/kivy-icon-96.png
mv kivy-icon-96.png icon.png
cd -
