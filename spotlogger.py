import spotipy, time, math, traceback, json, requests, os
from spotipy.oauth2 import SpotifyOAuth
import index_manager


with open("spotify_authentication.json", "r") as file:
    spotify_authentication = json.load(file)
    

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=spotify_authentication["client_id"],
                                            client_secret=spotify_authentication["client_secret"],
                                            redirect_uri=spotify_authentication["redirect_uri"],
                                            scope="user-library-read"))


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
            0,
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
                0,
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

    #print(f"Loaded 0 of {playlist_length}")

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
    track_id_pairs = []

    for track in tracks:
        artists = []
        for artist in track["artists"]:
            artists.append(artist["name"])

        matching_index = index_manager.album_exists(
            track["album"]["name"], 
            track["album"]["album_type"],
            artists
        )

        if matching_index:
            print(f"Found matching index {matching_index["ID"]} \"{matching_index["Name"]}\"")

            track_id_pairs.append(f"{matching_index["ID"]}_{track["track_number"]-1}")

            print(track["name"], track["track_number"]-1)
        else:
            print(f"Couldn't find \"{track["album"]["name"]}\" ({track["name"]})")

    
    with open("public/playlists/liked.csv", "w") as file:
        file.write(",".join(track_id_pairs))

    print("Saved Spotify liked playlist to local playlist")


def save_playlist(spotify_playlist_id):
    pl = sp.playlist(spotify_playlist_id)
    name = pl["name"]
    track_id_pairs = []

    for item in pl["tracks"]["items"]:
        track = item["track"]
        #print(track)
        artists = []
        for artist in track["artists"]:
            artists.append(artist["name"])

        print(artists)

        matching_index = index_manager.album_exists(
            track["album"]["name"], 
            track["album"]["album_type"],
            artists
        )

        if matching_index:
            print(f"Found matching index {matching_index["ID"]} \"{matching_index["Name"]}\"")

            track_id_pairs.append(f"{matching_index["ID"]}_{track["track_number"]-1}")

            print(track["name"], track["track_number"]-1)
        else:
            print(f"Couldn't find \"{track["album"]["name"]}\" ({track["name"]})")

    with open(f"public/playlists/{name}.csv", "w") as file:
        file.write(",".join(track_id_pairs))

#save_playlist("")

#save_liked_to_playlist()

#dingle_hole()

#register_albums_in_liked()

#register_album_spotify("4bOhT7b4ElXBkvdF7YqWnS")