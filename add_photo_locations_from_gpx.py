""" Add missing location information to photos in Apple Photos from a GPX file """


import sys
from bisect import bisect_left
from datetime import datetime
from functools import cached_property
from typing import Optional

import click
import gpxpy
from gpxpy.gpx import GPXTrackPoint
from osxphotos import PhotoInfo, PhotosDB
from osxphotos.photosalbum import PhotosAlbum
from osxphotos.utils import pluralize
from photoscript import PhotosLibrary

DEFAULT_TIME_DELTA = 60
LOCATION_HISTORY = None

__version__ = "0.02"


class GPXData:
    """Load GPX track points from a file and find nearest location to a given timestamp"""

    def __init__(self, file: str):
        self.file = file
        self.gpx = self._load_gpx(file)

    @cached_property
    def points(self) -> list[GPXTrackPoint]:
        """Return list of track points from GPX file (for example, one created with Geotag Photos Pro)"""
        # ignore waypoints without a time
        points = []
        for track in self.gpx.tracks:
            for segment in track.segments:
                points.extend([p for p in segment.points if p.time is not None])
        return sorted(points, key=lambda x: x.time)

    @cached_property
    def timestamps(self) -> list[datetime]:
        """Return list of timestamps from GPX file"""
        return [w.time for w in self.points]

    def _load_gpx(self, file: str):
        """Load GPX data from a file"""
        with open(file, "r") as f:
            gpx = gpxpy.parse(f)
        return gpx

    def nearest_location(self, timestamp: datetime):
        """Return tuple of (nearest location record, delta in sec) to given timestamp"""
        nearest = self._nearest_location_from_timestamp(timestamp)
        # find nearest waypoint with timestamp that matches
        point = next((w for w in self.points if w.time == nearest), None)
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
    dry_run: bool,
    album: Optional[PhotosAlbum] = None,
) -> int:
    """Add location information to photo record, returns 1 if location added, else 0"""
    nearest_location, nearest_delta = gpx_data.nearest_location(photo.date)
    nearest_delta = int(nearest_delta)
    if nearest_delta >= delta:
        return 0

    click.echo(
        f"Found location match for {photo.original_filename} taken on {photo.date} "
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
                click.echo(f"Error: could not access photo for uuid {photo.uuid}")
                return 0
            library_photo.location = (
                nearest_location.latitude,
                nearest_location.longitude,
            )
            click.echo("Added location to photo")
            if album:
                album.add(photo)
        except Exception as e:
            click.echo(f"Error: could not add location to photo {e}")
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
def main(gpx_filename, delta, dry_run, add_to_album, selected):
    """Add missing location data to photos in Apple Photos from GPX file."""
    click.echo(f"Version: {__version__}")
    click.echo(f"Loading GPX data from {gpx_filename}")
    gpx_data = GPXData(gpx_filename)
    if len(gpx_data.points) == 0:
        click.echo("No tracks found in GPX file.", err=True)
        sys.exit(1)
    click.echo(
        f"Loaded {len(gpx_data.points)} {pluralize(len(gpx_data.points), 'track point', 'track points')} from GPX file"
    )

    earliest = gpx_data.points[0]
    latest = gpx_data.points[-1]
    click.echo(f"Earliest: {earliest.time}, {earliest.latitude}, {earliest.longitude}")
    click.echo(f"Latest: {latest.time}, {latest.latitude}, {latest.longitude}")

    click.echo("Loading photo library")
    photosdb = PhotosDB()
    click.echo(f"Loaded {len(photosdb)} {pluralize(len(photosdb), 'photo', 'photos')}")

    if selected:
        selected_photos = PhotosLibrary().selection
        if not selected_photos:
            click.echo("No photos selected in Photos.", err=True)
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

    album = PhotosAlbum(add_to_album, verbose=click.echo) if add_to_album else None
    click.echo(
        f"Checking {len(photos)} {pluralize(len(photos), 'photo', 'photos')} "
        f"that lack{'s' if len(photos)==1 else ''} location information"
    )
    results = sum(
        add_location_to_photo(photo, gpx_data, delta, dry_run, album=album)
        for photo in photos
    )

    click.echo(
        f"Added location info to {results} {pluralize(results, 'photo', 'photos')}"
    )
    if add_to_album:
        click.echo(f"Added to album '{add_to_album}'")


if __name__ == "__main__":
    main()
