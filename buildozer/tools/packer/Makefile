.PHONY: all build
VERSION := 2.0
ANN1 = udp://public.popcorn-tracker.org:6969/announce
ANN2 = udp://ipv4.tracker.harry.lu/announce
ANN3 = udp://tracker.opentrackr.org:1337/announce
ANN4 = udp://9.rarbg.com:2710/announce
ANN5 = udp://explodie.org:6969
ANN6 = udp://tracker.coppersurfer.tk:6969
ANN7 = udp://tracker.leechers-paradise.org:6969
ANN8 = udp://zer0day.ch:1337
TORRENT_ANNOUNCE := ${ANN1},${ANN2},${ANN3},${ANN4},${ANN5},${ANN6},${ANN7},${ANN8}
PACKAGE_FILENAME = kivy-buildozer-vm-${VERSION}.zip

all: packer repackage torrent upload

build:
	packer-io build template.json

repackage:
	cd output-kivy-buildozer-vm && mv Kivy kivy-buildozer-vm-${VERSION}
	cd output-kivy-buildozer-vm && zip -0 -r ${PACKAGE_FILENAME} kivy-buildozer-vm-${VERSION}

torrent:
	rm -f output-kivy-buildozer-vm/kivy-buildozer-vm.torrent
	mktorrent \
		-a ${TORRENT_ANNOUNCE} \
		-o output-kivy-buildozer-vm/kivy-buildozer-vm.torrent \
		-w https://txzone.net/files/torrents/${PACKAGE_FILENAME} \
		-v output-kivy-buildozer-vm/${PACKAGE_FILENAME}

upload:
	# txzone only for now, don't have access to kivy server
	rsync -avz --info=progress2 output-kivy-buildozer-vm/${PACKAGE_FILENAME} txzone.net:/var/www/websites/txzone.net/files/torrents/
	rsync -avz --info=progress2 output-kivy-buildozer-vm/kivy-buildozer-vm.torrent txzone.net:/var/www/websites/txzone.net/files/torrents/
