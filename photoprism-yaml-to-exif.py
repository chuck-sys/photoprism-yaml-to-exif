from yaml import safe_load
try:
    # try for libyaml-based parser (faster)
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
import exiftool
import argparse
import logging
import os
import os.path
import bisect


FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
LOGGING_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
}
YAML_TO_EXIF = {
    'latitude': ['Lat', 'GPSLatitude'],
    'longitude': ['Lng', 'GPSLongitude'],
    'altitude': ['Alt', 'GPSAltitude*'],
    'iso': ['ISO', 'ISO'],
    'datetime_original': ['DateTimeOriginal', 'DateTimeOriginal'],
}


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='Photoprism YAML to EXIF',
        description='Convert Photoprism YAML sidecars to the original EXIF data.',
        epilog='Loosely based on https://github.com/JiCiT/photo_prism_yaml_to_exif Perl script.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        'sidecar_dir',
        help='Directory to the root sidecar.',
    )
    parser.add_argument(
        'photos_dir',
        help='Directory to the root photos.',
    )

    parser.add_argument(
        '--log-level',
        help='Logging level to show.',
        choices=LOGGING_LEVELS.keys(),
        required=False,
        default='info',
    )
    parser.add_argument(
        '--exiftool',
        help='Full path of exiftool if not in path.',
        required=False,
        default=None,
    )
    parser.add_argument(
        '--overwrite',
        help='Overwrite existing EXIF tag.',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=False,
    )

    parser.add_argument(
        '--latitude',
        help='Adjust latitude.',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        '--longitude',
        help='Adjust longitude.',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        '--altitude',
        help='Adjust altitude.',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        '--iso',
        help='Adjust original ISO',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        '--datetime-original',
        help='Adjust orginal date time.',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        '--create-date',
        help='Adjust create date.',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        '--dry-run',
        help='Say you are going to do it, but don\'t actually change any files.',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=False,
    )

    return parser


def do_the_file(eft: exiftool.ExifToolHelper, args: argparse.Namespace, sidecar_file: str, photos_file: str):
    with open(sidecar_file, 'r') as f:
        yaml_sidecar = safe_load(f, Loader=Loader)

    try:
        original_tags = eft.get_tags(photos_file)
    except exiftool.ExifToolExecuteError:
        logger.warning('Couldn\'t get tags from the original photo file {photos_file}')
        return

    tags_to_edit = {}
    for arg_name, data in YAML_TO_EXIF.items():
        sidecar_label, exif_label = data
        if args[arg_name] and sidecar_label in yaml_sidecar:
            if args.overwrite or exif_label not in original_tags:
                tags_to_edit[exif_label] = yaml_sidecar[sidecar_label]

    if 'Details' in yaml_sidecar:
        if 'Keywords' in yaml_sidecar['Details']:
            if 'Keywords' not in original_tags:
                tags_to_edit['Keywords'] = yaml_sidecar['Details']['Keywords'].split(', ')

    if args.dry_run:
        logger.info('Faking writing {len(tags_to_edit)} tags to file {photos_file}')
    else:
        try:
            eft.set_tags(
                photos_file,
                tags=tags_to_edit,
            )
            logger.info('Wrote {len(tags_to_edit)} tags to file {photos_file}')
        except exiftool.ExifToolExecuteError:
            logger.error('Could not write {len(tags_to_edit)} tags to file {photos_file}')


def traverse_dir(eft: exiftool.ExifToolHelper, args: argparse.Namespace, common_dirs: str, photos_dir: str):
    sidecar_files = sorted(os.listdir(os.path.join(args.sidecar_dir, common_dirs)))
    photos_files = os.listdir(os.path.join(args.photos_dir, common_dirs))

    for photos_file in photos_files:
        path, ext = os.path.splitext(photos_file)

        if os.path.isdir(os.path.join(args.photos_dir, common_dirs, photos_file)):
            index = bisect.bisect_left(sidecar_files, photos_file)
            if index < len(sidecar_files) and sidecar_files[index] == photos_file:
                traverse_dir(args, os.path.join(common_dirs, dir_basename))
            else:
                logger.debug(f'Skipping over directory {os.path.join(args.photos_dir, common_dirs, photos_file)}; could not find corresponding sidecar directory.')
        elif os.path.isfile(os.path.join(args.photos_dir, common_dirs, photos_file)):
            index = bisect.bisect_left(sidecar_files, path + '.yml')
            if index < len(sidecar_files) and sidecar_files[index] == path + '.yml':
                do_the_file(
                    args,
                    os.path.join(args.sidecar_dir, common_dirs, sidecar_files[index]),
                    os.path.join(args.photos_dir, common_dirs, photos_file),
                )
            else:
                logger.warning(f'Skipping over file {os.path.join(args.photos_dir, common_dirs, photos_file)}; could not find corresponding sidecar file')
        else:
            logger.debug(f'File {os.path.join(args.photos_dir, common_dirs, photos_file)} is neither a file nor a directory???')


def main():
    parser = get_parser()
    args = parser.parse_args()

    logger.setLevel(LOGGING_LEVELS[args.log_level])

    if not os.path.isdir(args.sidecar_dir):
        logger.error(f'Directory {args.sidecar_dir} does not exist!')
        return

    if not os.path.isdir(args.photos_dir):
        logger.error(f'Directory {args.photos_dir} does not exist!')
        return

    with exiftool.ExifToolHelper(executable=args.exiftool, logger=logger) as eft:
        traverse_dir(eft, args, '')


if __name__ == '__main__':
    main()
