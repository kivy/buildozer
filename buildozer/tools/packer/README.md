# Introduction

It is an example packer template based on netboot iso that adds packages for xubuntu and buildozer.

# Configure

You want to edit `http/preseed.cfg` and `template.json` before building an image.

# Build

`packer build template.json`

# Testing the image after it's built.

`./launch`

# TODO

  - [compact the image](https://crysol.github.io/recipe/2013-10-15/virtualbox-compact-vmdk-images/)
  - trigger a build on travis, torrent creation and gdrive upload when buildozer is released
  - https://www.packer.io/docs/builders/virtualbox-ovf.html
