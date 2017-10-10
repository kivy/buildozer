# Introduction

This is the packer template for building the official Kivy/Buildozer VM.
It is based on xubuntu.

# Configure

You want to edit `http/preseed.cfg` and `template.json` before building an image.

# Build

```
make packer
```

# Release

1. Update Makefile to increase the version number
2. Update the CHANGELOG
3. Commit

Then:

```
make all
# make packer       < build the image
# make repackage    < just zip it (no compression)
# make torrent      < create the torrent
# make upload       < upload on txzone.net (tito only)
```


# Notes

- trigger a build on travis, torrent creation and gdrive upload when buildozer is
  released
- https://www.packer.io/docs/builders/virtualbox-ovf.html
