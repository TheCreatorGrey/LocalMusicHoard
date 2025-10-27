import os, json


# Album index example
{
    "Type":"Album",
    "Name":"Pant shitter",
    "Release Year":1652,
    "Tracks":[
        {
            "Name":"Super Duper Pooper Scooper",
            "Artists":["Doo Doo Man"],
            "Audio":{ # Audio can also be null if there isn't any audio, only the registration
                "Format":".mp3",
                "Source":"YouTube", # The source of the audio
                "Verified":False # Whether or not it has been verified that the audio is correct
            }
        }
    ]
}



# Caches all album index files (also counts stuff)
index_cache = {}
def cache_indices():
    release_counter = 0
    track_counter = 0
    track_downloaded_counter = 0
    verified_counter = 0

    for index_file in os.listdir("public/indices"):
        with open("public/indices/" + index_file, "r") as file:
            index = json.load(file)
            index_cache[index["ID"]] = index

            # Counter shit
            release_counter += 1
            for track in index["Tracks"]:
                track_counter += 1

                if track["Audio"]:
                    track_downloaded_counter += 1

                    if track["Audio"]["Verified"]:
                        verified_counter += 1

    # Size measurement
    tracks_size_bytes = 0
    for track_name in os.listdir("public/tracks"):
        track_path = os.path.join("public/tracks", track_name)
        tracks_size_bytes += os.path.getsize(track_path)

    tracks_size_gb = round(tracks_size_bytes / 1000000000, 2) # woah-uh

    covers_size_bytes = 0
    for cover in os.listdir("public/covers"):
        cover_path = os.path.join("public/covers", cover)
        covers_size_bytes += os.path.getsize(cover_path)

    covers_size_gb = round(covers_size_bytes / 1000000000, 2)

    indices_size_bytes = 0
    for index in os.listdir("public/indices"):
        index_path = os.path.join("public/indices", index)
        indices_size_bytes += os.path.getsize(index_path)

    indices_size_kb = round(indices_size_bytes / 1000, 2)


    percent_downloaded = round((track_downloaded_counter/track_counter)*100)
    percent_verified = round((verified_counter/track_downloaded_counter)*100)
    print(f"\n\n=========== \\/ Totally awesomesauce music counter \\/ ===========")
    print(f"{release_counter} total registered releases")
    print(f"{track_counter} total registered tracks")
    print(f"{track_downloaded_counter} ({percent_downloaded}%) are downloaded")
    print(f"{verified_counter} ({percent_verified}%) of downloaded tracks are verified")

    print(f"\nDownloaded tracks take up {tracks_size_gb} GB")
    print(f"Downloaded covers take up {covers_size_gb} GB")
    print(f"Downloaded covers take up {covers_size_gb} GB")
    print(f"Release indices take up {indices_size_kb} KB")
    print(f"================================================================\n\n")

cache_indices()

# Saves the cached data for an album to its file
# INDEX FOR ALBUM SHOULD BE CACHED BEFORE SAVING
def save_album_index(album_id):
    with open(f"public/indices/{album_id}.json", "w") as file:
        json.dump(index_cache[album_id], file)
    
    print(f"Cached data for album #{album_id} ({index_cache[album_id]["Name"]}) saved to file")

# Saves the cached data for all albums to their respective files
def save_all_album_indices():
    for album_id in index_cache:
        save_album_index(album_id)


# Pretty obvious innit mate bruv
def get_contributing_artists(album):
    artists = []

    for track in album["Tracks"]:
        for artist in track["Artists"]:
            if artist not in artists:
                artists.append(artist)

    return artists


# Returns the first album ID which isn't taken
def first_available_album_id():
    new_album_id = 0
    while new_album_id in index_cache:
        new_album_id += 1

    return new_album_id


# Checks if there is already an album in the index with a matching name, type, and at least one common artist
def album_exists(name, release_type, artists):
    for album_id in index_cache:
        album = index_cache[album_id]
        if name == album["Name"]: # Name matches
            if release_type.lower() == album["Type"].lower(): # Type matches
                # Check for matching artists
                for artist in artists:
                    if artist in get_contributing_artists(album):
                        # If both are so, the album is likely already indexed
                        return album



# Adds an empty album with information into the index and returns it
# REGISTERING AN ALBUM THAT IS ALREADY INDEXED WILL ERASE THE CURRENT INDEX; WHETHER AN ALBUM IS ALREADY INDEXED OR NOT SHOULD BE CHECKED BEFORE CALLING
def register_album(name, release_type, release_year, number_of_tracks, cover_data):
    # Before the album index is created, get the cover first so we can store the cover ID

    album_id = first_available_album_id()
    print(album_id)

    if cover_data:
        # Write data to file with album ID as the name so the cover can be found using its ID
        with open(f"public/covers/{album_id}.jpeg", "wb") as file:
            file.write(cover_data)


    # Now actually make the album index
    index_cache[album_id] = {
        "Type":release_type,
        "Name":name,
        "Release Year":release_year,
        "Tracks":[],
        "ID":album_id
    }

    return index_cache[album_id]