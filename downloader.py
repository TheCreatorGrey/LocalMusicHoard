from pytubefix import YouTube, Search
import index_manager, os

def yt_download_track(album_id, track_number, overwrite=False, video_url=None, save_index=True):
    album = index_manager.index_cache[album_id]
    file_name = f"{album_id}_{track_number}.mkv"

    track = album["Tracks"][track_number]

    print(f"Downloading \"{track["Name"]}\" by {" ".join(track["Artists"])} from \"{album["Name"]}\"...")

    if track["Audio"]:
        print("Track already has audio")
        if overwrite:
            print("Overwriting current audio...")
        else:
            print("Track will not be overwritten")
            return
    else:
        track["Audio"] = { # Add audio information
            "Format":".mkv",
            "Source":"YouTube",
            "Verified":False
        }

    # Search for track if url is not given
    if video_url:
        url = video_url
    else:
        query = f"{track["Name"]} by {" ".join(track["Artists"])} Audio"

        result = Search(query).videos[0]
        url = result.watch_url

    video = YouTube(url)
    stream = video.streams.get_audio_only()
    stream.download(output_path="public/tracks/", filename=file_name)

    # Reset audio information 
    track["Audio"]["Format"] = ".mkv"
    track["Audio"]["Source"] = "YouTube"
    track["Audio"]["Verified"] = False

    if save_index:
        index_manager.save_album_index(album_id)


#downloadAlbum("3fdvtN6S22HXlEAqX3OHqz", 30)
#downloadLiked(40)

# Downloads the tracks in a registered album from YouTube
def fill_album(album_id):
    album = index_manager.index_cache[album_id]

    for track_num in range(len(album["Tracks"])):
        yt_download_track(album_id, track_num)

#fill_album("V")


def dl_singles_from_artist(index, artist_name):
    for release in index["Albums"]:
        if release["Type"] == "Single":
            if artist_name in index_manager.get_contributing_artists(release):
                yt_download_track(release, 0)