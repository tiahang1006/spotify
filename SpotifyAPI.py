from utils.__apPy__ import apPy
from utils.WebFlow import WebFlow
import pandas as pd
import numpy as np

class SpotifyAPI:
    client_key = "9e5d4d5a6a9748fc9832e7d7c773c91c"
    client_secret = "21675db2ce8a487da844970932c7a6de"
    # track_features = ["track.name", "track.explicit", "track.id", "track.popularity"]
    # track_attr_features = ["trackAttrs.acousticness", "trackAttrs.danceability", "trackAttrs.duration_ms", "trackAttrs.energy", "trackAttrs.instrumentalness", "trackAttrs.key", "trackAttrs.liveness", "trackAttrs.loudness", "trackAttrs.mode", "trackAttrs.speechiness", "trackAttrs.tempo", "trackAttrs.time_signature"]
    # artist_features = ["artist.genres", "artist.name", "artist.id", "artist.popularity"]
    features = [
        "track.id", "artist.id", "artist.name", "track.name", "addedAt", "track.popularity", "artist.popularity", "artist.genres", "track.explicit",

        "trackAttributes.duration_ms", "trackAttributes.tempo", "trackAttributes.mode", "trackAttributes.key",
        "trackAttributes.time_signature", "trackAttributes.loudness",
        "trackAttributes.acousticness", "trackAttributes.danceability", "trackAttributes.energy",
        "trackAttributes.instrumentalness", "trackAttributes.liveness",
        "trackAttributes.speechiness",
    ]

    def __init__(self):
        """
        Creates and authorizes an instance of the SpotifyAPI
        """
        self.api = self.__generateStaticAPI__(self.__fetchToken__())

    def getUserTracks(self, maxTracks=5000):
        tracksDict, addedAt = self.__loadUserSavedTracks__(maxTracks)
        featuresDict = self.__loadTrackFeatures__(list(tracksDict.keys()))
        artistDict = self.__getArtists__(tracksDict)
        return self.__formatResults__(tracksDict, addedAt, featuresDict, artistDict)

    def getTrackData(self, trackID, megaDict):
        arr = []
        artistID = megaDict["track"][trackID]
        for f in SpotifyAPI.features:
            if f == "addedAt":
                arr.append(megaDict["addedAt"][trackID])
            else:
                obj, attr = f.split(".")
                arr.append(megaDict[obj][trackID][attr])
        return np.array(arr)

    def __formatResults__(self, tracksDict, addedAt, featuresDict, artistDict):
        megaDict = {}
        megaDict["track"] = tracksDict
        megaDict["addedAt"] = addedAt
        megaDict["trackAttributes"] = featuresDict
        megaDict["artist"] = artistDict
        tracks = np.array([self.getTrackData(t, megaDict) for t in tracksDict.keys()])
        df = pd.DataFrame(tracks, columns=SpotifyAPI.features)
        return df


    def __addTracksToDict__(self, tracks, d, keyGetter, objGetter):
        # for t in tracks: d[keyGetter(t)] = t
        for t in tracks: d[keyGetter(t)] = objGetter(t)
        return d

    def __loadUserSavedTracks__(self, maxTracks=float("inf")):
        lastCall = self.api.saved_tracks(limit=50)
        tracks = self.__addTracksToDict__(lastCall.items, {}, lambda t: t.track.id, lambda t: t.track)
        addedAt = self.__addTracksToDict__(lastCall.items, {}, lambda t: t.track.id, lambda t: t.added_at)
        # res = lastCall.items
        while hasattr(lastCall, "next") and len(tracks) < maxTracks:
            try:
                lastCall = self.api.saved_tracks(limit=50, offset = lastCall.offset + 50)
                # res.extend(lastCall.items)
                self.__addTracksToDict__(lastCall.items, tracks, lambda t: t.track.id, lambda t: t.track)
                self.__addTracksToDict__(lastCall.items, addedAt, lambda t: t.track.id, lambda t: t.added_at)
                print(f"Got ({len(tracks)} / {lastCall.total}) tracks so far!")
            except:
                break
        print("DONE")
        return tracks, addedAt

    def __loadTrackFeatures__(self, ids):
        i = 0
        tracksPerRequest = 100
        res = {}
        while i < len(ids):
            nextIDs = ids[i:i + tracksPerRequest]
            i += tracksPerRequest
            nextIDs = ",".join(nextIDs)
            q = self.api.features(ids=nextIDs)
            # return q
            self.__addTracksToDict__(q.audio_features, res, lambda t: t.id, lambda t: t)
        return res

    def __getArtists__(self, trackDict : dict):
        artistIDs = list(set([artist.id for t in trackDict.values() for artist in t.artists]))
        i = 0
        tracksPerRequest = 50
        res = {}
        while i < len(artistIDs):
            nextIDs = artistIDs[i:i + tracksPerRequest]
            i += tracksPerRequest
            nextIDs = ",".join(nextIDs)
            q = self.api.artists(ids=nextIDs)
            # return q
            self.__addTracksToDict__(q.artists, res, lambda t: t.id, lambda t: t)
        return self.__artistDictToTrackDict__(trackDict, res)

    def __artistDictToTrackDict__(self, trackDict, artistDict):
        d = {}
        for t in trackDict.keys():
            artists = [artistDict[a.id] for a in trackDict[t].artists]
            d[t] = {}
            d[t]["id"] = ",".join([a.id for a in artists])
            d[t]["name"] = ",".join([a.name for a in artists])
            d[t]["popularity"] = ",".join([str(a.popularity) for a in artists])
            d[t]["genres"] = ",".join(list(set([g for a in artists for g in a.genres])))
        return d
            # d[t]["id, name, popularity, genres,"]


    def __fetchToken__(self):
        w = WebFlow("https://accounts.spotify.com")
        return w.authorization_flow(
            endpoint="/authorize",
            token_key='access_token',
            client_id=SpotifyAPI.client_key,
            response_type="token",
            redirect_uri="https://elleklinton.com/spotify",
            scope="playlist-read-private playlist-modify-public playlist-modify-private playlist-read-collaborative user-library-read user-read-email".replace(" ", "%20")
        )

    def __generateStaticAPI__(self, token):
        header = {
            'Authorization': 'Bearer {0}'.format(token),
            'Content-Type': 'application/json'
        }
        api = apPy(base_url='https://api.spotify.com/v1')
        api.add_endpoint(endpoint_name='search', endpoint='/search', protocol='GET', header=header)
        api.add_endpoint(endpoint_name="me", endpoint="/me", protocol="GET", header=header)
        api.add_endpoint(endpoint_name="saved_tracks", endpoint="/me/tracks", protocol="GET", header=header)
        api.add_endpoint(endpoint_name="features", endpoint="/audio-features", protocol="GET", header=header)
        api.add_endpoint(endpoint_name="artists", endpoint="/artists", protocol="GET", header=header)
        api.header = header
        return api

api = SpotifyAPI()

t = api.getUserTracks()
t.to_csv("Ellek-Liked-Tracks.csv")