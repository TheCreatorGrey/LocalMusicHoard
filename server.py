import os, index_manager, downloader, playlog, json, base64, spotlogger, random
import http
import signal

# I am completely aware of how abysmal some of the code in here is but really I'm doing this project for myself so uhhhhhh yeah

# Create directories that don't come with the repo if they don't already exist
os.makedir("bals_man", exist_ok=True)
#os.makedir("analytics", exist_ok=True)
#os.makedir("indices", exist_ok=True)
#os.makedir("covers", exist_ok=True)
#os.makedir("tracks", exist_ok=True)

playlog.load()
running = True

def processRequest(raw):
    global running

    data = json.loads(raw)
    #print(data)

    # I had to make a function for this because it raises an error when you try
    # to get an item from a dict that doesnt exist instead of returning null like JS does
    def arg(id):
        if id in data:
            return data[id]
        else:
            return None
    
    intent = arg("intent")

    print(f"Request with intent to {intent}")


    if intent == "close_server": # Turns off server
        close_server()
        return True

    if intent == "shutdown": # Turns off host machine
        os.system('shutdown')
        return True


    # Information

    if intent == "get_index_ids":
        return list(index_manager.index_cache.keys())

    if intent == "get_track_info_from_id":
        album = index_manager.index_cache[arg("album_id")]
        track = album["Tracks"][arg("track_num")]
        return track

    if intent == "get_album_info_from_id":
        album = index_manager.index_cache[arg("id")]
        return album

    if intent == "get_albums_including_artist":
        id_list = []
        for album_id in index_manager.index_cache:
            if arg("name") in index_manager.get_contributing_artists(album_id):
                id_list.append(album_id)

        return id_list

    if intent == "get_playlist_names":
        name_list = []
        for file_name in os.listdir("public/playlists"):
            name_list.append(file_name.split(".csv")[0])

        return name_list


    if intent == "search_tracks": # Basic track search
        query = arg("query").lower()
        results = []

        for album_id in index_manager.index_cache:
            album = index_manager.index_cache[album_id]
            for track in album["Tracks"]:
                if (query in track["Name"].lower()):
                    results.append([album_id, track["Track Number"]])

        return results

    if intent == "get_top_tracks":
        listen_counts = {}

        with open("public/analytics/playlog.json") as file:
            data = json.loads(file.read())
            for listen in data["local"]:
                ref_code = f"{listen[0]}_{listen[1]}"

                if ref_code in listen_counts:
                    listen_counts[ref_code] += 1
                else:
                    listen_counts[ref_code] = 0

        print(listen_counts)

        return sorted(listen_counts, key=listen_counts.get, reverse=True)


    # Automatic indexing / registering

    if intent == "spot_register_album": # Automatically register album from Spotify
        spotlogger.register_album_spotify(arg("spotify_album_id"))
        return True

    if intent == "spot_register_playlist": # Automatically register album from Spotify
        spotlogger.register_album_spotify(arg("spotify_pl_id"))
        return True


    # Automatic downloading

    if intent == "yt_dl_by_url": # Download audio for track from youtube url
        downloader.yt_download_track(arg("album_id"), arg("track_num"), True, arg("url"))
        index_manager.add_write_list(arg("album_id"))
        return True

    if intent == "yt_search_track": # Finds possible url for track on youtube
        return downloader.yt_search_track(arg("album_id"), arg("track_num"))

    if intent == "dl_by_search_album":
        album_id = arg("album_id")
        album = index_manager.index_cache[album_id]

        for track_num in range(len(album["Tracks"])):
            downloader.yt_download_track(album_id, track_num, save_index=False)

        #index_manager.save_album_index(album_id)
        index_manager.add_write_list(album_id)

        return True


    # Information updating

    if intent == "new_playlist": # NOT CURRENTLY USED. REMOVE LATER
        with open(f"/playlists/{arg("name")}.csv") as file:
            pass

    if intent == "add_track_to_playlist":
        with open(f"/playlists/{arg("name")}.csv", "a") as file: # Append data to playlist file. Create if it doesn't exist
            file.write(f",{arg("album_id")}_{arg("track_id")}")

    if intent == "new_index": # Creates an empty release/album index and sends the ID
        new_index = index_manager.register_album(arg("name"), arg("type"), arg("year"), arg("track_count"), None)
        return new_index["ID"]

    if intent == "add_track": # Adds empty track to album/release
        album = index_manager.index_cache[arg("album_id")]

        album["Tracks"].append({
            "Name": arg("name"), 
            "Artists": arg("artists").split(","), 
            "Track Number": len(album["Tracks"]), 
            "Audio": None
        })

    if intent == "set_audio":
        file_type = arg("file_type")

        album = index_manager.index_cache[arg("album_id")]
        track = album["Tracks"][arg("track_num")]

        with open(f"public/tracks/{arg("album_id")}_{arg("track_num")}{file_type}", "wb") as file:
            # Since everything is being sent in JSON, the file needs to be sent from the client as a base 64 data url
            raw = base64.b64decode(arg("data_url"))
            file.write(raw)

        # Update index

        if not track["Audio"]:
            track["Audio"] = {}

        track["Audio"]["Format"] = file_type
        track["Audio"]["Source"] = "Unknown"
        track["Audio"]["Verified"] = False

        index_manager.add_write_list(arg("album_id"))

    if intent == "set_cover":
        with open(f"public/covers/{arg("album_id")}.jpeg", "wb") as file:
            raw = base64.b64decode(arg("data_url"))
            file.write(raw)

    if intent == "set_verification":
        verified = arg("bool")
        
        album = index_manager.index_cache[arg("album_id")]
        track = album["Tracks"][arg("track_num")]

        if track["Audio"]:
            track["Audio"]["Verified"] = verified
            index_manager.add_write_list(arg("album_id"))

            return True

    if intent == "set_name":
        album = index_manager.index_cache[arg("album_id")]
        track = album["Tracks"][arg("track_num")]

        track["Name"] = arg("name")

    if intent == "set_artists":
        album = index_manager.index_cache[arg("album_id")]
        track = album["Tracks"][arg("track_num")]

        track["Artists"] = arg("artists").split(",")


    # Reccomendations and random track finding

    if intent == "reccommend_next_track":
        album = index_manager.index_cache[arg("album_id")]

        # First go through album of track and get the first of the following tracks with audio
        for track in album["Tracks"]:
            if arg("track_num") < track["Track Number"]:
                if track["Audio"]:
                    if not playlog.was_played_recently("local", album["ID"], track["Track Number"], 10):
                        return [album["ID"], track["Track Number"]]

        # If that doesn't work, find another album with the same artist with a track that has audio
        for album_id in index_manager.index_cache:
            album_check = index_manager.index_cache[album_id]
            contributing_this = index_manager.get_contributing_artists(album["ID"])
            contributing_other = index_manager.get_contributing_artists(album_id)

            # See if there is at least one common artist
            for artist in contributing_this:
                if artist in contributing_other:

                    # Try to find first track with audio

                    for track in album_check["Tracks"]:
                        if track["Audio"]:
                            if not playlog.was_played_recently("local", album_id, track["Track Number"], 10):
                                return [album_id, track["Track Number"]]

        # And if that STILL DOESN'T WORK, just give em a random track

        album_ids = list(index_manager.index_cache.keys())
        random.shuffle(album_ids)

        for album_id in album_ids:
            album = index_manager.index_cache[album_id]
            
            for track in album["Tracks"]:
                if track["Audio"]:
                    if not playlog.was_played_recently("local", album_id, track["Track Number"], 10):
                        return [album_id, track["Track Number"]]
                        

    if intent == "log_play": # Sent by the client when a track is played telling the server to add to the play log
        playlog.add("local", arg("album_id"), arg("track_num"))
        return True



class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length'))
        body = self.rfile.read(content_length)

        path_split = self.path.split("/")

        print(path_split)

        if path_split[1] == "api":
            self.send_response(200)
            self.send_header("Content-type", "application/json")

            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate") # Stops browsers from caching, ideal for development
            self.send_header("Expires", "0")

            self.end_headers()
            

            print(body)
            response = json.dumps({"response":processRequest(body)})

            self.wfile.write(bytes(response, "utf8"))

        elif path_split[1] == "upload":

            # For audio or cover uploads
            # Path format is /upload/audio/album_id/track_id
            album_id = int(path_split[3])
            track_id = int(path_split[4])

            if path_split[2] == "audio":
                pass

            if path_split[2] == "cover":
                pass


print("Server is running now")
server = http.server.ThreadingHTTPServer(("", 80), Handler)
#server.serve_forever()


def close_server(sig=None, frame=None): # Args are only here so this function can be passed to signal. They don't serve any purpose
    print("Server is closing now...")

    playlog.save()
    index_manager.save_write_list()
    running = False
    sys.exit()

signal.signal(signal.SIGINT, close_server) # Gracefully close server upon ctrl+C or other forceful shutdown


while running:
    server.handle_request()