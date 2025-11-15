async function request(data) {
    console.log(data)
    var response = await fetch(`/api`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    }).catch(() => {
        console.error("Request failed.")
        return undefined
    })

    if (response) {
        response = await response.json()
        console.log(response)
        return response.response;
    }
}


function truncate_title(title, limit) {
    if (limit < title.length) {
        return title.substring(0, limit-3) + "..."
    } else {
        return title
    }
}


const icon = document.getElementById("icon");
const content_area = document.getElementById("content_area");
const album_cover = document.getElementById("album_cover");
const playback_bar = document.getElementById("playback_bar");
const now_playing_title = document.getElementById("now_playing_title");
const audio_controls = document.getElementById("audio");
const audio_source = document.getElementById("audio_source");

document.title = "Music Library - Nothing Playing"




let session_play_history = [];
let currently_playing_album_id = 0;
let currently_playing_track_number = 0;
async function play(album_id, track_number) {
    currently_playing_album_id = album_id
    currently_playing_track_number = track_number
    console.log(currently_playing_album_id)

    // Add to play log
    request({"intent":"log_play", "album_id":album_id, "track_num":track_number});

    let info = await request({"intent":"get_track_info_from_id", "album_id":album_id, "track_num":track_number});
    audio_source.src = `tracks/${album_id}_${track_number}${info.Audio.Format}`;
    audio_controls.load();
    audio_controls.play();

    let cover_source = `covers/${album_id}.jpeg`;
    album_cover.src = cover_source;
    icon.href = cover_source;

    let title = `${info.Name} - ${info.Artists[0]}`;
    document.title = title;
    now_playing_title.innerText = title;

    // Adding the track to a list allows the user to play previous tracks
    session_play_history.push([album_id, track_number])
}

async function play_next() {
    let next_track = await request({
        "intent":"reccommend_next_track", 
        "album_id":currently_playing_album_id, 
        "track_num":currently_playing_track_number
    });

    await play(next_track[0], next_track[1])
}

async function play_previous() {
    if (0 < session_play_history.length) {
        // Remove the currently playing track so the previous is in front and is played
        session_play_history.pop();
        last_track = session_play_history[session_play_history.length-1]
        play(last_track[0], last_track[1]);
        // The play function will have added this track to the history making two adjacent copies in the history list.
        // If the user tries to go back again, the same track will play. Remove so this doesnt happen
        session_play_history.pop();
    }
}

audio_controls.onended = () => {
    play_next()
}





function clear_menu() {
    content_area.innerHTML = "";
}

async function add_track_card(album_id, track_number) {
    let track_info = await request({"intent":"get_track_info_from_id", "album_id":album_id, "track_num":track_number});

    let track_container = document.createElement("div");
    track_container.className = "track_container";

    let cover_source = `covers/${album_id}.jpeg`;
    let cover = document.createElement("img");
    cover.className = "inline_cover"
    cover.src = cover_source;
    track_container.appendChild(cover);

    let play_btn = document.createElement("img");
    play_btn.className = "inline_button"
    play_btn.src = "./assets/play.svg";
    track_container.appendChild(play_btn);

    let track_text = document.createElement("span");
    track_text.className = "track_text"
    track_container.appendChild(track_text);

    let track_title = document.createElement("div");
    track_title.innerText = truncate_title(track_info.Name, 40);
    track_text.appendChild(track_title);


    let track_artists = document.createElement("div");
    track_artists.classList = "track_artists";
    //track_artists.innerText = truncate_title(track_info.Artists.join(", "), 40);

    for (artist of track_info.Artists) {
        let artist_link = document.createElement("span");
        artist_link.innerText = artist + ", ";
        artist_link.setAttribute("onclick", `load_artist_page("${artist}")`);
        track_artists.appendChild(artist_link)
    }

    track_text.appendChild(track_artists);


    if (!track_info.Audio) {
        track_text.style.color = "grey"
    }

    // Adding a function to the event like () => {} instead of function () captures the variable values at the time it is assigned
    play_btn.onclick = async () => {
        console.log(album_id, track_number);
        play(album_id, track_number)
    }

    let button_area = document.createElement("span");
    track_container.appendChild(button_area);

    track_container.onmouseenter = () => {
        let verify_btn = document.createElement("img");
        verify_btn.className = "inline_button"
        verify_btn.src = "./assets/unverified.svg";
        verify_btn.title = "Verify that the audio for this track is correct";
        button_area.appendChild(verify_btn);

        if (track_info["Audio"]) {
            if (track_info["Audio"]["Verified"]) {
                verify_btn.src = "./assets/verified.svg"
            }
        }
    
        verify_btn.onclick = () => {
            if (track_info["Audio"]["Verified"]) {
                track_info["Audio"]["Verified"] = false
                verify_btn.src = "./assets/unverified.svg"
                request({"intent":"set_verification", "album_id":album_id, "track_num":track_number, "bool":false})
            } else {
                track_info["Audio"]["Verified"] = true
                verify_btn.src = "./assets/verified.svg"
                request({"intent":"set_verification", "album_id":album_id, "track_num":track_number, "bool":true})
            }
            
        }    
    
        let dl_from_url_btn = document.createElement("img");
        dl_from_url_btn.className = "inline_button"
        dl_from_url_btn.src = "./assets/download_from_link.svg";
        dl_from_url_btn.title = "Automatically download audio for this track from pasted URL";
        button_area.appendChild(dl_from_url_btn);
    
        dl_from_url_btn.onclick = async () => {
            let url = document.getElementById("url_box").value;
            console.log(url);
            await request({"intent":"redownload", "album_id":album_id, "track_num":track_number, "url":url});
            track_text.style.color = "white"
        }
    
    
        let track_dl_bysearch_btn = document.createElement("img");
        track_dl_bysearch_btn.className = "inline_button"
        track_dl_bysearch_btn.src = "./assets/download_from_search.svg";
        track_dl_bysearch_btn.title = "Automatically download audio for this track by searching";
        button_area.appendChild(track_dl_bysearch_btn);
    
        track_dl_bysearch_btn.onclick = async () => {
            await request({"intent":"dl_by_search", "album_id":album_id, "track_num":track_number});
            track_text.style.color = "white"
        }
    }

    track_container.onmouseleave = () => {
        button_area.innerHTML = "";
    }

    content_area.appendChild(track_container);
}






async function load_artist_page(artist) {
    clear_menu();

    let head_text = document.createElement("h1");
    head_text.className = "header_text"
    head_text.innerText = artist
    content_area.appendChild(head_text);

    let album_ids = await request({"intent":"get_albums_including_artist", "name":artist});

    for (let id of album_ids) {
        let album = await request({"intent":"get_album_info_from_id", "id":id});

        // Yeah I get this is inefficient but who cares bro its a local server

        for (let track_number=0; track_number<album.Tracks.length; track_number++) {
            add_track_card(id, track_number)
        }
    }
}

async function load_playlist_page(name) {
    clear_menu();

    let head_text = document.createElement("h1");
    head_text.className = "header_text"
    head_text.innerText = name
    content_area.appendChild(head_text);

    let response_raw = await fetch(`playlists/${name}.csv`);
    let response_text = await response_raw.text();
    let playlist = response_text.split(",");

    for (let id_pair of playlist) {
        console.log(id_pair)
        let id_pair_seperate = id_pair.split("_");
        let album_id = parseInt(id_pair_seperate[0]);
        let track_number = parseInt(id_pair_seperate[1]);

        await add_track_card(album_id, track_number)
    }
}

load_playlist_page("liked");



// This basically controls what happens when you press buttons on the media controls in the device notifications
navigator.mediaSession.setActionHandler('nexttrack', play_next);
navigator.mediaSession.setActionHandler('previoustrack', play_previous);