#!/usr/bin/env python3
from . import SpotifyStreamer

import urllib.parse
import click
import requests
import sys
import json
import select

from deezer import Deezer
from deezer import TrackFormats
from deemix.types.Track import Track
from deemix import generateDownloadObject, parseLink
from deemix.settings import DEFAULTS as DEFAULT_SETTINGS, load as loadSettings
from deemix.downloader import getPreferredBitrate, formatsName, streamTrack
from deemix.errors import DownloadFailed, MD5NotFound, \
    DownloadCanceled, PreferredBitrateNotFound, \
    TrackNot360, AlbumDoesntExists,  \
    DownloadError, DownloadEmpty, \
    ErrorMessages

from deezer.errors import WrongLicense, WrongGeolocation

from deemix.types.DownloadObjects import Single, Collection
from deemix.utils import USER_AGENT_HEADER
from deemix.utils.crypto import _md5, _ecbCrypt, _ecbDecrypt, generateBlowfishKey, decryptChunk
from deemix.types.DownloadObjects import Single, Collection, Convertable

dz = Deezer()
settings = DEFAULT_SETTINGS
plugins = {}
seen = set()

def fan_dl_object(downloadObject, plugs, bitrate, greedy=False, keep_going=False):
    stack = [downloadObject];

    while len(stack):
        downloadObject = stack.pop()

        if isinstance(downloadObject, list):
            stack.extend(downloadObject)

        elif isinstance(downloadObject, Single):
            extraData = {
                'trackAPI': downloadObject.single.get('trackAPI'),
                'albumAPI': downloadObject.single.get('albumAPI'),
            }

            link = extraData["trackAPI"]["link"]
            if greedy and not link in seen:
                seen.add(link)
                yield (downloadObject, extraData)

            if not greedy:
                yield (downloadObject, extraData)

        elif isinstance(downloadObject, Convertable):
            obj = plugs[downloadObject.plugin].convert(dz, downloadObject, settings)
            stack.append(obj)

        elif isinstance(downloadObject, Collection):
            for track in downloadObject.collection['tracks']:
                album_uri = None
                #album_uri = track["album"]["tracklist"].rsplit("/", 1)[0]
                if "album" in track and "tracklist" in track["album"]:
                    album_uri = track["album"]["tracklist"]
                # link = track["link"]

                extraData = {
                    'trackAPI': track,
                    'albumAPI': downloadObject.collection.get('albumAPI'),
                    'playlistAPI': downloadObject.collection.get('playlistAPI')
                }

                if greedy and not link in seen:
                    seen.add(link)
                    yield (downloadObject, extraData)

                # if greedy and not album_uri in seen:
                #     seen.add(album_uri)
                # try:
                #     downloadObject = generateDownloadObject(dz, album_uri, bitrate, plugins=plugs)
                #     stack.append(downloadObject)
                #     continue
                # except Exception as err:
                #     jerr(err)

                if not greedy:
                    yield (downloadObject, extraData)

def metadata(downloadObject, extraData, bitrate=TrackFormats.MP3_320):
    albumAPI = extraData.get('albumAPI')
    playlistAPI = extraData.get('playlistAPI')
    trackAPI = extraData.get('trackAPI')
    trackAPI['size'] = downloadObject.size

    json.dump(trackAPI, sys.stdout)
    print("", file=sys.stdout)
    sys.stdout.flush()


def stream_input(urls):
    for x in urls:
        yield x

    if select.select([sys.stdin, ], [], [], 0.0)[0]:
        for line in sys.stdin:
            yield line.strip()

@click.command()
@click.option('-a', '--arl', type=str, default=None, help='ARL token to use')
@click.option('-s', '--spt-id', type=str, help='Path to the config folder')
@click.option('-ss', '--spt-secret', type=str, help='Path to the config folder')
@click.option('-sc', '--spt-cache', type=str, help='Path to the config folder')
@click.option('-k', '--keep-going', is_flag=True, help='Path to the config folder')
@click.option('-g', '--greedy', is_flag=True, help='Path to the config folder')
@click.argument('urls', nargs=-1, required=False)
def metadata_cli_caller(urls, arl, spt_id, spt_secret, spt_cache, keep_going, greedy):
    assert arl, 'You must provide an ARL token'
    assert dz.login_via_arl(arl.strip()), 'Invalid ARL'

    settings = DEFAULT_SETTINGS

    plugins = {"spotify": SpotifyStreamer(spt_id, spt_secret, spt_cache)}
    plugins["spotify"].setup()

    bitrate = settings.get("maxBitrate", TrackFormats.MP3_320)

    jerr = lambda e: json.dump({
        "error": {
          "name": e.__class__.__name__,
          "reason": str(e)
        }
    }, sys.stderr)


    for url in stream_input(urls):
        print("debug main")
        (link, _link_type, _link_id) = parseLink(url)
        try:
            downloadObject = generateDownloadObject(dz, link, bitrate, plugins=plugins)
        except Exception as err:
            jerr(err)
            if not keep_going:
                exit(1)

        for (obj, extras) in list(fan_dl_object(downloadObject, plugins, bitrate, greedy)):
            try:
                metadata(obj, extras)
            except Exception as err:
                jerr(err)

@click.command()
@click.option('-a', '--arl', type=str, default=None, help='ARL token to use')
@click.option('-s', '--spt-id', type=str, help='Path to the config folder')
@click.option('-ss', '--spt-secret', type=str, help='Path to the config folder')
@click.option('-sc', '--spt-cache', type=str, help='Path to the config folder')
@click.option('-k', '--keep-going', is_flag=True, help='Path to the config folder')
@click.option('-g', '--greedy', is_flag=True, help='Path to the config folder')
@click.argument('urls', nargs=-1, required=False)
def stream_cli_caller(urls, arl, spt_id, spt_secret, spt_cache, keep_going, greedy):
    assert arl, 'You must provide an ARL token'
    assert dz.login_via_arl(arl.strip()), 'Invalid ARL'

    settings = DEFAULT_SETTINGS

    plugins = {"spotify": SpotifyStreamer(spt_id, spt_secret, spt_cache)}
    plugins["spotify"].setup()

    bitrate = settings.get("maxBitrate", TrackFormats.MP3_320)

    jerr = lambda e: json.dump({
        "error": {
          "name": e.__class__.__name__,
          "reason": str(e)
        }
    }, sys.stderr)


    for url in stream_input(urls):
        (link, _link_type, _link_id) = parseLink(url)
        try:
            downloadObject = generateDownloadObject(dz, link, bitrate, plugins=plugins)
        except Exception as err:
            jerr(err)
            if not keep_going: exit(1)

        for (obj, extras) in list(fan_dl_object(downloadObject, plugins, bitrate, greedy)):
            try:
                metadata(obj, extras)
            except Exception as err:
                jerr(err)

def metadata_cli():
    metadata_cli_caller(auto_envvar_prefix='DEEMIX')

def stream_cli():
    metadata_cli_caller(auto_envvar_prefix='DEEMIX')

if __name__ == '__main__':
    metadata_cli_caller(auto_envvar_prefix='DEEMIX')
