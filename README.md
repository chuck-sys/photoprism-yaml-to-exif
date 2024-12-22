Inspired by [the original](https://github.com/JiCiT/photo_prism_yaml_to_exif), but I don't know Perl that
well, and I couldn't get it to run, so I made my own.

After writing this and [checking for a script that does Google Photos][gp], I have a feeling that you can
just use the `exiftool` itself instead of writing another script. I haven't tried it before, but it might
work. Or might not, unless you convert from YAML to JSON.

[gp]: https://exiftool.org/forum/index.php?topic=12361.0

# Dependencies

- Python 3
- [PyExifTool](https://github.com/sylikc/pyexiftool)
- [ExifTool](https://exiftool.org/)
- [pyyaml](https://pyyaml.org/wiki/PyYAMLDocumentation)

```console
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

# Usage

This is just the help text.

```
usage: photoprism-yaml-to-exif.py [-h]
                                  [--log-level {debug,info,warning,error}]
                                  [--exiftool EXIFTOOL]
                                  [--overwrite | --no-overwrite]
                                  [--latitude | --no-latitude]
                                  [--longitude | --no-longitude]
                                  [--altitude | --no-altitude]
                                  [--iso | --no-iso]
                                  [--datetime-original | --no-datetime-original]
                                  [--details | --no-details]
                                  [--dry-run | --no-dry-run]
                                  sidecar_dir photos_dir

Convert Photoprism YAML sidecars to the original EXIF data.

positional arguments:
  sidecar_dir           Directory to the root sidecar.
  photos_dir            Directory to the root photos.

options:
  -h, --help            show this help message and exit
  --log-level {debug,info,warning,error}
                        Logging level to show. (default: info)
  --exiftool EXIFTOOL   Full path of exiftool if not in path. (default: None)
  --overwrite, --no-overwrite
                        Overwrite existing EXIF tag. (default: False)
  --latitude, --no-latitude
                        Adjust latitude. (default: True)
  --longitude, --no-longitude
                        Adjust longitude. (default: True)
  --altitude, --no-altitude
                        Adjust altitude. (default: True)
  --iso, --no-iso       Adjust original ISO (default: True)
  --datetime-original, --no-datetime-original
                        Adjust orginal date time. (default: True)
  --details, --no-details
                        Adjust orginal details (keywords only). (default:
                        True)
  --dry-run, --no-dry-run
                        Say you are going to do it, but don't actually change
                        any files. (default: False)

Loosely based on https://github.com/JiCiT/photo_prism_yaml_to_exif Perl
script.
```

# Examples

If you wanna do a dry run, a normal non-dry run, and then delete all the originals:

```console
(venv) $ # Don't write to file; check to make sure that there are no important errors
(venv) $ python --dry-run photoprism-yaml-to-exif.py /datadrive/photoprism/storage/sidecar /home/user/Pictures
(venv) $ # Do it!
(venv) $ python photoprism-yaml-to-exif.py /datadrive/photoprism/storage/sidecar /home/user/Pictures
(venv) $ # Remove the original files
(venv) $ find /home/user/Pictures -name '*_original' -delete
```

If you wanna do a normal run, and then you wanted to tweak the code a bit so you restored the files:

```console
(venv) $ python photoprism-yaml-to-exif.py /datadrive/photoprism/storage/sidecar /home/user/Pictures
(venv) $ # Undo undo undo!
(venv) $ exiftool -restore_original /home/user/Pictures
```
