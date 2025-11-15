import spotipy, time, math, traceback, json, requests, os
from spotipy.oauth2 import SpotifyOAuth
import index_manager
from pprint import pprint


with open("spotify_authentication.json", "r") as file:
    spotify_authentication = json.load(file)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=spotify_authentication["client_id"],
                                            client_secret=spotify_authentication["client_secret"],
                                            redirect_uri=spotify_authentication["redirect_uri"],
                                            scope="user-library-read"))


def register_track(track):
    track_album = track["album"]
    album_name = track["album"]["name"]

    album_artists = []
    for artist in track["album"]["artists"]:
        album_artists.append(artist["name"])


    match = None
    for index_album in index["Albums"]:

        if index_album["Name"] == track_album["name"]: # Name matches

            # Check if track album and album in index have matching artists
            for artist in track_album["artists"]:
                if artist["name"] in index_album["Artists"]:
                    # If both are so, the index album and the album of the track likely match
                    match = index_album
        

    if match:
        print(f'Found matching album for "{match["Name"]}" in index.')
        album_index = match

    else:
        print(f'Album for track "{track["name"]}" not found in index yet. Creating...')

        # Before the album index is created, get the cover first so we can store the cover ID

        cover_data = None

        # TAKE OUT OF IF FALSE LATER \/\/\/\/\/
        if False:
            if 0 < len(track["album"]["images"]):
                # Get the smallest resolution cover so we don't eat up space with thousands of high res covers
                smallest_cover = None
                for cover in track["album"]["images"]:
                    if smallest_cover:
                        if (cover["width"] < smallest_cover["width"]):
                            smallest_cover = cover
                    else:
                        smallest_cover = cover

                try:
                    cover_data = requests.get(smallest_cover["url"], timeout=10).content
                except requests.exceptions.Timeout:
                    print("Request for cover timed out")
        # /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
        

        if 0 < len(track["album"]["images"]):
            cover_data = True

        # Now actually make the album index
        album_index = index_manager.register_album(
            track["album"]["name"],
            track["album"]["album_type"].capitalize(),
            track["album"]["release_date"].split("-")[0],
            track["album"]["total_tracks"],
            cover_data
        )


    # Now that the album index has been found or created, there is somewhere to put the track

    tracks = sp.album(track_album["id"])["tracks"]["items"]
    print(tracks)
    track_num = 0
    for t in tracks:
        track_artists = []
        for artist in t["artists"]:
            track_artists.append(artist["name"])

        album_index["Tracks"].append(
            {
                "Name":t["name"],
                "Artists":track_artists,
                "Track Number":track_num,
                "Audio Asset ID":None
            }
        )

        track_num += 1



# Gets the albums of songs in the Spotify liked songs list. May return duplicates for now
def albums_in_liked(playlist_length=1472, chunk_size=40, cooldown=1):
    print("Retrieving albums in Spotify liked list...")

    num_chunks = math.ceil(playlist_length/chunk_size)

    albums = []
    album_ids = []
    offset = 0

    print(f"Loaded 0 of {playlist_length}")

    for i in range(num_chunks):
        results = sp.current_user_saved_tracks(chunk_size, offset)
        for idx, item in enumerate(results['items']):
            album_id = item["track"]["album"]["id"]

            if album_id not in album_ids:
                album_ids.append(album_id)
                albums.append(item["track"]["album"])

        print(f"Loaded {offset} of {playlist_length}", end='\r')
        offset += chunk_size
        time.sleep(cooldown)

    return albums


# Registers an album from spotify ID
def register_album_spotify(album_id):
    album = spotify_album_full(album_id)

    release_type = album["album_type"].capitalize()
    tracks = album["tracks"]["items"]

    # \/ This makes a list of contributing artists for the spotify album
    # so it can be compared with the other indexed albums to see if it
    # is indexed already. The list of artists the API gives us is 
    # unreliable because for some stupid ass reason Spotify labels any
    # release with more than four contributing artists with "Various Artists"

    album_artists = []
    for track in tracks:
        for artist in track["artists"]:
            if artist["name"] not in album_artists:
                album_artists.append(artist["name"])

    existing_album_index = index_manager.album_exists(
        album["name"],  
        release_type,
        album_artists
    )

    if existing_album_index:
        album_index = existing_album_index
        print(f'"{album["name"]}" is already indexed')

    else:
        print(f'"{album["name"]}" is not indexed yet - indexing now...')

        cover_data = None
        if 0 < len(album["images"]):
            # Get the smallest resolution cover so we don't eat up space with thousands of high res covers
            largest_cover = album["images"][0]

            try:
                cover_data = requests.get(largest_cover["url"], timeout=10).content
            except requests.exceptions.Timeout:
                print("Request for cover timed out")

        album_index = index_manager.register_album(
            album["name"],
            release_type,
            album["release_date"].split("-")[0],
            album["total_tracks"],
            cover_data
        )

    #print(tracks)
    track_num = 0
    for track in tracks:
        track_artists = []
        for artist in track["artists"]:
            track_artists.append(artist["name"])

        album_index["Tracks"].append(
            {
                "Name":track["name"],
                "Artists":track_artists,
                "Track Number":track_num,
                "Audio": None
            }
        )

        track_num += 1
    
    index_manager.save_album_index(album_index["ID"])


def register_albums_in_liked():
    albums = albums_in_liked()

    for album in albums:
        release_type = album["album_type"].capitalize()
        tracks = sp.album(album["id"])["tracks"]["items"]

        # \/ This makes a list of contributing artists for the spotify album
        # so it can be compared with the other indexed albums to see if it
        # is indexed already. The list of artists the API gives us is 
        # unreliable because for some stupid ass reason Spotify labels any
        # release with more than four contributing artists with "Various Artists"

        album_artists = []
        for track in tracks:
            for artist in track["artists"]:
                if artist["name"] not in album_artists:
                    album_artists.append(artist["name"])

        existing_album_index = index_manager.album_exists(
            album["name"],  
            release_type,
            album_artists
        )

        if existing_album_index:
            album_index = existing_album_index
            print(f'"{album["name"]}" is already indexed')

        else:
            print(f'"{album["name"]}" is not indexed yet - indexing now...')

            cover_data = None
            if 0 < len(album["images"]):
                cover_data = True

            album_index = index_manager.register_album(
                album["name"],
                release_type,
                album["release_date"].split("-")[0],
                album["total_tracks"],
                cover_data
            )

            #print(tracks)
            for track in tracks:
                track_artists = []
                for artist in track["artists"]:
                    track_artists.append(artist["name"])

                album_index["Tracks"].append(
                    {
                        "Name":track["name"],
                        "Artists":track_artists,
                        "Audio Asset ID":None,
                        "Audio Source":None,
                        "Audio Format":None
                    }
                )




def get_tracks_in_liked(playlist_length):
    print("Retrieving tracks in Spotify liked list...")

    chunk_size = 40
    cooldown = .5

    num_chunks = math.ceil(playlist_length/chunk_size)

    tracks = []
    offset = 0

    print(f"Loaded 0 of {playlist_length}")

    for i in range(num_chunks):
        results = sp.current_user_saved_tracks(chunk_size, offset)
        for idx, item in enumerate(results['items']):
            tracks.append(item["track"])

        #print(f"Indexed {offset} of {playlist_length}", end='\r')
        offset += chunk_size
        time.sleep(cooldown)

    return tracks

# Behaves like spotipy.album but it returns all tracks in the album, not just up to the limit of 50
def spotify_album_full(album_id):
    print("Retrieving tracks in Spotify album...")

    album = sp.album(album_id)
    album_length = album["tracks"]["total"]
    print(album_length)

    # Extends current response with missing tracks past the limit
    if album["tracks"]["limit"] < album["tracks"]["total"]:
        chunk_size = 40
        offset = album["tracks"]["limit"]
        cooldown = .5

        

        num_chunks = math.ceil(album_length/chunk_size)

        for i in range(num_chunks):
            results = sp.album_tracks(album_id, chunk_size, offset)
            for idx, item in enumerate(results['items']):
                album["tracks"]["items"].append(item)
                print(item["name"])

            offset += chunk_size
            time.sleep(cooldown)

    print(len(album["tracks"]["items"]))

    return album


def save_liked_to_playlist():
    tracks = get_tracks_in_liked(1486) # 1486
    file_text = ""

    for track in tracks:
        # get list of artists

        artists = []
        for artist in track["artists"]:
            artists.append(artist["name"])

        #print(artists)

        matching_index = index_manager.album_exists(
            track["album"]["name"], 
            track["album"]["album_type"],
            artists
        )

        if matching_index:
            print(f"Found matching index {matching_index["ID"]} \"{matching_index["Name"]}\"")

            file_text += f"{matching_index["ID"]}_{track["track_number"]-1},"

            print(track["name"], track["track_number"]-1)
        else:
            print(f"Couldn't find \"{track["album"]["name"]}\" ({track["name"]})")

    
    with open("public/playlists/liked.csv", "w") as file:
        file.write(file_text)

    print("Saved Spotify liked playlist to local playlist")

#save_liked_to_playlist()

#dingle_hole()

#register_albums_in_liked()

#register_album_spotify("6XFk5NEkZ45fez4714U3bV")
#register_album_spotify("0XC7fNm2tr27w7nIE8WbMD")
#register_album_spotify("5oPvIsJd6pzjmpvmiSVbjg")

#register_album_spotify("10VePcOVEROqtHiBGquI2A")


register_album_spotify("1bdgMcE3UokVZ9y8fU2Auz")