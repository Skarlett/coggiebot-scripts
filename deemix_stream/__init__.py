#!/usr/bin/env python3

#!/usr/bin/env python3
from deemix.types.DownloadObjects import Single, Collection, Convertable
from deemix.plugins.spotify import Spotify
import spotipy

#######################
# Patch for SSL error #
#######################
from os import environ
environ['CURL_CA_BUNDLE'] = ""
environ['REQUESTS_CA_BUNDLE'] = ""

SpotifyClientCredentials = spotipy.oauth2.SpotifyClientCredentials
CacheFileHandler = spotipy.cache_handler.CacheFileHandler

class MockCache(dict):
    def __getitem__(self, _key):
        return {}

class SpotifyStreamer(Spotify):
    def __init__(self, id, secret, auth_cache, cache_file=None):
        super().__init__(None)
        self.credentials = {
            "clientId": id,
            "clientSecret": secret,
        }
        self.auth_cache = auth_cache
        self.cache_file = cache_file

    def setup(self):
        self.checkCredentials()
        return self

    def loadCache(self):
        return MockCache()

    def saveCache(self, newCache):
        with open(self.cache_file, 'w', encoding="utf-8") as spotifyCache:
            json.dump(newCache, spotifyCache)

    def loadCache(self):
        cache = None
        if (self.cache_file).is_file():
            with open(self.cache_file, 'r', encoding="utf-8") as f:
                try:
                    cache = json.load(f)
                except json.decoder.JSONDecodeError:
                    self.saveCache({'tracks': {}, 'albums': {}})
                    cache = None
                except Exception:
                    cache = None
        if not cache: cache = {'tracks': {}, 'albums': {}}
        return cache

    def checkCredentials(self):
        if self.credentials['clientId'] == "" or self.credentials['clientSecret'] == "":
            self.enabled = False
            return

        try:
            cache_handler = CacheFileHandler(self.auth_cache)
            client_credentials_manager =SpotifyClientCredentials(
                client_id=self.credentials['clientId'],
                client_secret=self.credentials['clientSecret'],
                cache_handler=cache_handler
            )

            self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            self.sp.user_playlists('spotify')
            self.enabled = True
        except Exception:
            self.enabled = False
