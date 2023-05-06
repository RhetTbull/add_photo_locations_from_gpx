""" Add missing location information to photos in Apple Photos from a GPX file """

from __future__ import annotations

import sys
from bisect import bisect_left
from datetime import datetime, timedelta
from functools import cached_property
from textwrap import dedent
from typing import Optional

import click
import gpxpy
from gpxpy.gpx import GPXTrackPoint
from osxphotos import PhotoInfo, PhotosDB
from osxphotos.cli.param_types import TimeOffset
from osxphotos.datetime_utils import (
    datetime_naive_to_utc,
    datetime_remove_tz,
    datetime_utc_to_local,
)
from osxphotos.photosalbum import PhotosAlbum
from osxphotos.utils import pluralize
from photoscript import PhotosLibrary
from rich import print

DEFAULT_TIME_DELTA = 60
LOCATION_HISTORY = None

__version__ = "0.2.0"


def gpx_datetime_to_local(dt: datetime) -> datetime:
    """Convert a GPX datetime to local datetime

    GPX datetime is UTC but may have timezone SimpleTZ("Z")

    Args:
        dt: timezone aware datetime.datetime object in UTC

    Returns:
        timezone aware datetime.datetime object in local timezone
    """
    return datetime_utc_to_local(datetime_naive_to_utc(datetime_remove_tz(dt)))


class GPXData:
    """Load GPX track points from a file and find nearest location to a given timestamp"""

    def __init__(self, file: str):
        self.file = file
        self.gpx = self._load_gpx(file)

    @cached_property
    def points(self) -> list[GPXTrackPoint]:
        """Return list of track points from GPX file (for example, one created with Geotag Photos Pro)"""
        # ignore track points without a time
        points = []
        for track in self.gpx.tracks:
            for segment in track.segments:
                points.extend([p for p in segment.points if p.time is not None])
        return sorted(points, key=lambda x: x.time)

    @cached_property
    def timestamps(self) -> list[datetime]:
        """Return list of timestamps from GPX file"""
        return [p.time for p in self.points]

    def _load_gpx(self, file: str):
        """Load GPX data from a file"""
        with open(file, "r") as f:
            gpx = gpxpy.parse(f)
        return gpx

    def nearest_location(self, timestamp: datetime):
        """Return tuple of (nearest location record, delta in sec) to given timestamp"""
        nearest = self._nearest_location_from_timestamp(timestamp)
        # find nearest waypoint with timestamp that matches
        point = next((p for p in self.points if p.time == nearest), None)
        return point, abs((point.time - timestamp).total_seconds())

    def _nearest_location_from_timestamp(self, timestamp: datetime) -> datetime:
        """Given a timestamp as datetime, find nearest (in time) location record"""
        i = bisect_left(self.timestamps, timestamp)
        return min(
            self.timestamps[max(0, i - 1) : i + 2],
            key=lambda t: abs(timestamp - t),
        )

    def __len__(self):
        return len(self.points)


def add_location_to_photo(
    photo: PhotoInfo,
    gpx_data: GPXData,
    delta: int,
    offset: timedelta | None,
    dry_run: bool,
    album: Optional[PhotosAlbum] = None,
) -> int:
    """Add location information to photo record, returns 1 if location added, else 0"""
    date = photo.date + offset if offset is not None else photo.date
    nearest_location, nearest_delta = gpx_data.nearest_location(date)
    nearest_delta = int(nearest_delta)

    if nearest_delta >= delta:
        return 0

    offset_str = (
        f" (offset by {offset.total_seconds()} seconds = {date})"
        if offset is not None
        else ""
    )
    print(
        f"Found location match for {photo.original_filename} taken on {photo.date}{offset_str} "
        f"within {nearest_delta} seconds: "
        f"{nearest_location.latitude}, {nearest_location.longitude}"
    )
    if not dry_run:
        try:
            photolib = PhotosLibrary()
            library_photo = photolib.photos(uuid=[photo.uuid])
            if library_photo:
                library_photo = list(library_photo)[0]
            else:
                print(f"Error: could not access photo for uuid {photo.uuid}")
                return 0
            library_photo.location = (
                nearest_location.latitude,
                nearest_location.longitude,
            )
            print("Added location to photo")
            if album:
                album.add(photo)
        except Exception as e:
            print(f"Error: could not add location to photo {e}")
            return 0
    return 1


@click.command()
@click.argument("gpx_filename", type=click.Path(exists=True))
@click.option(
    "--delta",
    type=int,
    default=DEFAULT_TIME_DELTA,
    help=f"Time delta in seconds, default = {DEFAULT_TIME_DELTA}.",
)
@click.option(
    "--offset",
    type=TimeOffset(),
    help=dedent(
        """Time offset of your photos from the timestamp in the GPX file.
    Date/time stamps in the GPX file are specified in UTC timezone.
    If you import a photo without a timezone into Photos, Photos will assume the photo is in your local timezone
    at the time of the import. This script will use the timezone information in the Photos library to correctly
    compare to the UTC date/time in the GPX file. However, if the datetime information in the Photos library is
    not correct, you can specify an offset to shift the date/time for comparison. For example, if you were in
    UTC timezone when you took the photos but then imported the photos into Photos while you were in the EST
    timezone, Photos would assume the photos were taken in EST timezone and the Photos date/time would actually
    be 5 hours earlier than the UTC date/time in the GPX file.
    --offset may thus be required to shift the date/time in Photos to match the GPX date/time.
    For example, if your local timezone is UTC-5 (EST) you can specify "--offset '-5 hours'" to shift the date/time
    in Photos by 5 hours before comparing to the GPX file.
    The offset time can be specified in a number of formats, for example "--offset -05:00:00" which is in (HH:MM:SS)
    format. If your timezone is ahead of UTC, you would use a positive offset, for example --offset +02:00:00.
    This option may also be useful if the camera clock was off by a certain amount of time.
    Valid format for date/time offset: '±HH:MM:SS', '±H hours' (or hr), '±M minutes' (or min), '±S seconds' (or sec), '±S' (where S is seconds)
    """
    ),
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Dry run, do not actually update location info for photos.",
)
@click.option(
    "--add-to-album",
    metavar="ALBUM",
    help="Add updated photos to album named ALBUM, creating the album if necessary.",
)
@click.option(
    "--selected",
    is_flag=True,
    help="Only update photos currently selected in Photos. "
    "Default is to update all photos with missing location data in the library.",
)
def main(gpx_filename, delta, offset, dry_run, add_to_album, selected):
    """Add missing location data to photos in Apple Photos from GPX file."""
    print(f"Version: {__version__}")
    print(f"Offset: {offset}")
    print(f"Loading GPX data from {gpx_filename}")
    gpx_data = GPXData(gpx_filename)
    if len(gpx_data.points) == 0:
        print("No tracks found in GPX file.", err=True)
        sys.exit(1)
    print(
        f"Loaded {len(gpx_data.points)} {pluralize(len(gpx_data.points), 'track point', 'track points')} from GPX file"
    )

    earliest = gpx_data.points[0]
    latest = gpx_data.points[-1]
    print(
        f"Earliest: {earliest.time} ({gpx_datetime_to_local(earliest.time)}), {earliest.latitude}, {earliest.longitude}"
    )
    print(
        f"Latest: {latest.time} ({gpx_datetime_to_local(latest.time)}), {latest.latitude}, {latest.longitude}"
    )

    print("Loading photo library")
    photosdb = PhotosDB()
    print(f"Loaded {len(photosdb)} {pluralize(len(photosdb), 'photo', 'photos')}")

    if selected:
        selected_photos = PhotosLibrary().selection
        if not selected_photos:
            print("No photos selected in Photos.", err=True)
            sys.exit(1)
        photos = [
            photo
            for photo in photosdb.photos(uuid=[p.uuid for p in selected_photos])
            if photo.location == (None, None) and not photo.shared
        ]
    else:
        photos = [
            photo
            for photo in photosdb.photos()
            if photo.location == (None, None) and not photo.shared
        ]

    album = PhotosAlbum(add_to_album, verbose=print) if add_to_album else None
    print(
        f"Checking {len(photos)} {pluralize(len(photos), 'photo', 'photos')} "
        f"that lack{'s' if len(photos)==1 else ''} location information"
    )
    results = sum(
        add_location_to_photo(photo, gpx_data, delta, offset, dry_run, album=album)
        for photo in photos
    )

    print(
        f"Added location info to {results} {pluralize(results, 'photo', 'photos')}"
    )
    if add_to_album:
        print(f"Added to album '{add_to_album}'")


if __name__ == "__main__":
    main()
