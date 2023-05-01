# Add location to Apple Photos from GPX File

Python script to add missing location data to photos in your Apple Photos library based on a data from a GPX file. This script can be run stand-alone to add location data to the photos in your library or via [osxphotos](https://github.com/RhetTbull/osxphotos) using the `osxphotos run` command.

## Installation

Clone the repo:

- `git clone https://github.com/RhetTbull/add_photo_locations_from_gpx.git`
- `cd add_photo_locations_from_gpx`

I recommend you create and activate a python [virtual environment](https://docs.python.org/3/library/venv.html) before running pip:

- `python3 -m venv venv`
- `source venv/bin/activate`

Then install requirements:

- `python3 -m pip requirements.txt`

Requires python 3.9+

Alternatively, you can just install osxphotos using [these instructions](https://github.com/RhetTbull/osxphotos#installation) then run the script using `osxphotos run add_photo_locations_from_gpx.py`.

## Running

```
python3 add_photo_locations_from_gpx.py --help

or, if running with osxphotos:

osxphotos run add_photo_locations_from_gpx.py --help

Usage: add_photo_locations_from_gpx.py [OPTIONS] FILENAME

Options:
  --delta INTEGER       Time delta in seconds, default = 60.
  --dry-run             Dry run, do not actually update location info for
                        photos.
  --add-to-album ALBUM  Add updated photos to album named ALBUM, creating the
                        album if necessary.
  --help                Show this message and exit.
```

I strongly recommend you run with `--dry-run` first and manually check the locations for some of the photos.  I also recommend using the `--add-to-album` to add all updated photos to an album so you can check the results.  

`--delta` specifies how close in time (in seconds) the GPX timestamp needs to be (in seconds) in order to match the location to the photo's timestamp.

## Caveat

This script can modify photos in your Photos library. Use with caution.  No warranty is implied or provided.
