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

def fan_dl_object(downloadObject, plugs):
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
            yield (downloadObject, extraData)

        elif isinstance(downloadObject, Convertable):
            obj = plugs[downloadObject.plugin].convert(dz, downloadObject, settings)
            stack.append(obj)

        elif isinstance(downloadObject, Collection):
            for track in downloadObject.collection['tracks']:
                extraData = {
                    'trackAPI': track,
                    'albumAPI': downloadObject.collection.get('albumAPI'),
                    'playlistAPI': downloadObject.collection.get('playlistAPI')
                }
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
@click.argument('urls', nargs=-1, required=False)
def metadata(urls, arl, spt_id, spt_secret, spt_cache):
    assert arl, 'You must provide an ARL token'
    assert dz.login_via_arl(arl.strip()), 'Invalid ARL'

    settings = DEFAULT_SETTINGS
    
    plugins = {"spotify": SpotifyStreamer(spt_id, spt_secret, spt_cache)}
    plugins["spotify"].setup()
    
    bitrate = settings.get("maxBitrate", TrackFormats.MP3_320)

    jerr = lambda e: json.dump({
        "error": {
          "name": e.__class__.__name__,
          "reason": urllib.parse.quote(e.message)
        }
    }, sys.stderr)


    for url in stream_input(urls):
        (link, _link_type, _link_id) = parseLink(url)
        try:
            downloadObject = generateDownloadObject(dz, link, bitrate, plugins=plugins)
        except Exception as err:
            jerr(err)
            exit(1)

        for (obj, extras) in list(fan_dl_object(downloadObject, plugins)):
            try:
                metadata(obj, extras)
            except Exception as err:
                jerr(err)

@click.command()
@click.option('-a', '--arl', type=str, default=None, help='ARL token to use')
@click.option('-s', '--spt-id', type=str, help='Path to the config folder')
@click.option('-ss', '--spt-secret', type=str, help='Path to the config folder')
@click.option('-sc', '--spt-cache', type=str, help='Path to the config folder')
@click.argument('urls', nargs=-1, required=False)
def stream(urls, arl, spt_id, spt_secret, spt_cache):
    assert arl, 'You must provide an ARL token'
    assert dz.login_via_arl(arl.strip()), 'Invalid ARL'

    settings = DEFAULT_SETTINGS

    plugins = {"spotify": SpotifyStreamer(spt_id, spt_secret, spt_cache)}
    plugins["spotify"].setup()

    bitrate = settings.get("maxBitrate", TrackFormats.MP3_320)

    jerr = lambda e: json.dump({
        "error": {
          "name": e.__class__.__name__,
          "reason": urllib.parse.quote(e.message)
        }
    }, sys.stderr)


    for url in stream_input(urls):
        (link, _link_type, _link_id) = parseLink(url)
        try:
            downloadObject = generateDownloadObject(dz, link, bitrate, plugins=plugins)
        except Exception as err:
            jerr(err)
            exit(1)

        for (obj, extras) in list(fan_dl_object(downloadObject, plugins)):
            try:
                metadata(obj, extras)
            except Exception as err:
                jerr(err)

if __name__ == '__main__':
    main(auto_envvar_prefix='DEEMIX')
