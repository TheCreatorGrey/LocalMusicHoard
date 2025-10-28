from flask import Flask, request, send_from_directory, json
#from waitress import serve
import os, requests, index_manager, downloader

HOST = "0.0.0.0"

server = Flask(__name__)

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

        index_manager.save_album_index(album_id)

        return True

    if intent == "set_verification":
        verified = arg("bool")
        
        album = index_manager.index_cache[arg("album_id")]
        track = album["Tracks"][arg("track_num")]

        if track["Audio"]:
            track["Audio"]["Verified"] = verified

            return True


@server.route('/api', methods=['POST'])
def api():
    return {"response":processRequest(request.data)}

if __name__ == '__main__':
    server.run("0.0.0.0", port=80)
    print("Server is running now")