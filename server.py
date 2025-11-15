from flask import Flask, request, send_from_directory, json
import os, requests, index_manager, downloader, playlog

# I am completely aware of how abysmal some of the code in here is but really I'm doing this project for myself so uhhhhhh yeah

HOST = "0.0.0.0"

server = Flask(__name__)

playlog.load()

@server.route('/')
@server.route('/<path:filename>')
def index(filename=''):
    if not filename \
        or filename.endswith('/') \
        or os.path.isdir(os.path.join("public", filename)):
        
        filename = os.path.join(filename, 'index.html')
    return send_from_directory("public", filename)

def processRequest(raw):
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



    if intent == "get_indices":
        return index_manager.index_cache

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



    if intent == "redownload":
        downloader.yt_download_track(arg("album_id"), arg("track_num"), True, arg("url"))

        return True

    if intent == "dl_by_search":
        downloader.yt_download_track(arg("album_id"), arg("track_num"), True)

        return True

    if intent == "dl_by_search_album":
        album_id = arg("album_id")
        album = index_manager.index_cache[album_id]

        for track_num in range(len(album["Tracks"])):
            downloader.yt_download_track(album_id, track_num, save_index=False)

        #index_manager.save_album_index(album_id)
        index_manager.add_write_list(album_id)

        return True



    if intent == "set_verification":
        verified = arg("bool")
        
        album = index_manager.index_cache[arg("album_id")]
        track = album["Tracks"][arg("track_num")]

        if track["Audio"]:
            track["Audio"]["Verified"] = verified
            index_manager.add_write_list(arg("album_id"))

            return True


    # Others

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

        # And if that STILL DOESN'T WORK, just give em the first track with audio that can be found

    if intent == "log_play": # Sent by the client when a track is played telling the server to add to the play log
        playlog.add("local", arg("album_id"), arg("track_num"))
        return True


@server.route('/api', methods=['POST'])
def api():
    return {"response":processRequest(request.data)}


print("Server is running now")
server.run("0.0.0.0", port=80)

playlog.save()

index_manager.save_write_list()