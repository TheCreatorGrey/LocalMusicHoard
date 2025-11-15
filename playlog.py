import json, os
from datetime import datetime

# Keeps a history of played tracks if you want to make some sort of spotify wrapped thing or something

path = "public/analytics/playlog.json"

log = {}
def load():
    global log # I really hate doing that but it seems to have fixed it so whatever

    if os.path.exists(path):
        with open(path, "r") as file:
            log = json.load(file)

        print("Track play log loaded")

def add(profile_name, album_id, track_num):
    if profile_name not in log:
        log[profile_name] = []

    date = datetime.today()

    # Log album ID, track number and date to profile
    log[profile_name].append(
        [album_id, track_num, date.day, date.month, date.year] # Fine, I'll use day-month-year.
    )

# Checks whether a track was played recently. Used when finding the next tracks to play
def was_played_recently(profile_name, album_id, track_num, limit=10):
    recent_tracks = log[profile_name][-limit:]

    for track in recent_tracks:
        if track[0] == album_id:
            if track [1] == track_num:
                return True

    return False


def save():
    with open(path, "w") as file:
        json.dump(log, file)

    print("Track play log saved")