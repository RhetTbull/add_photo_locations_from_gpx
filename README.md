# Add location to Apple Photos from GPX File
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-2-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

Python script to add missing location data to photos in your Apple Photos library based on a data from a GPX file. This script can be run stand-alone to add location data to the photos in your library or via [osxphotos](https://github.com/RhetTbull/osxphotos) using the `osxphotos run` command.

## Installation

The easiest way to run this is to install [osxphotos](https://github.com/RhetTbull/osxphotos) using [these instructions](https://github.com/RhetTbull/osxphotos#installation)
and run the script using:

      osxphotos run https://raw.githubusercontent.com/RhetTbull/add_photo_locations_from_gpx/refs/heads/main/add_photo_locations_from_gpx.py FILENAME.gpx

To see the help for the script, run:

      osxphotos run https://raw.githubusercontent.com/RhetTbull/add_photo_locations_from_gpx/refs/heads/main/add_photo_locations_from_gpx.py --help

You can also save the script locally and run it:

      osxphotos run add_photo_locations_from_gpx.py FILENAME.gpx

If you're comfortable with python, you can also run this script stand-alone:

Clone the repo:

- `git clone git@github.com:RhetTbull/add_photo_locations_from_gpx.git`
- `cd add_photo_locations_from_gpx`

I recommend you create and activate a python [virtual environment](https://docs.python.org/3/library/venv.html) before running pip:

- `python3 -m venv venv`
- `source venv/bin/activate`

Then install requirements:

- `python3 -m pip -r requirements.txt`

Requires python 3.9+

## Running

```
python3 add_photo_locations_from_gpx.py --help

or, if running with osxphotos:

osxphotos install gpxpy
osxphotos run add_photo_locations_from_gpx.py --help

Usage: add_photo_locations_from_gpx.py [OPTIONS] GPX_FILENAME

  Add missing location data to photos in Apple Photos from GPX file.

Options:
  --delta INTEGER       Time delta in seconds, default = 60.
  --dry-run             Dry run, do not actually update location info for
                        photos.
  --add-to-album ALBUM  Add updated photos to album named ALBUM, creating the
                        album if necessary.
  --selected            Only update photos currently selected in Photos.
                        Default is to update all photos with missing location
                        data in the library.
  --help                Show this message and exit.
```

I strongly recommend you run with `--dry-run` first and manually check the locations for some of the photos.  I also recommend using the `--add-to-album` to add all updated photos to an album so you can check the results.

`--delta` specifies how close in time (in seconds) the GPX timestamp needs to be (in seconds) in order to match the location to the photo's timestamp.

Photos which already have a location in Photos will not be updated even if the photo's time matches a time in the GPX file.

## License

MIT License. See [LICENSE](LICENSE) file.

## Dependencies

- [osxphotos](https://github.com/RhetTbull/osxphotos)
- [gpxpy](https://github.com/tkrajina/gpxpy)

## See Also

- [add_photo_locations_from_google_history](https://github.com/RhetTbull/add_photo_locations_from_google_history)

## Caveat

This script can modify photos in your Photos library. Use with caution. No warranty is implied or provided.

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="http://www.kevinyank.com/"><img src="https://avatars.githubusercontent.com/u/89772?v=4?s=100" width="100px;" alt="Kevin Yank"/><br /><sub><b>Kevin Yank</b></sub></a><br /><a href="https://github.com/RhetTbull/add_photo_locations_from_gpx/commits?author=sentience" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://entorb.net"><img src="https://avatars.githubusercontent.com/u/59419684?v=4?s=100" width="100px;" alt="Torben"/><br /><sub><b>Torben</b></sub></a><br /><a href="https://github.com/RhetTbull/add_photo_locations_from_gpx/commits?author=entorb" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
