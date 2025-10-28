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


let currently_playing_album_id = 0;
let currently_playing_track_number = 0;
async function play(album_id, track_number, play_next=true) {
    currently_playing_album_id = album_id
    currently_playing_track_number = track_number
    console.log(currently_playing_album_id)

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

    if (play_next) {
        audio_controls.onended = () => {
            play(
                currently_playing_album_id, 
                currently_playing_track_number+1,
                true
            )
        }
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
    track_artists.innerText = truncate_title(track_info.Artists.join(", "), 40);
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
    
        verify_btn.onclick = () => {
            if (track["Audio"]["Verified"]) {
                track["Audio"]["Verified"] = false
                verify_btn.src = "./assets/unverified.svg"
                request({"intent":"set_verification", "album_id":album_id, "track_num":track_number, "bool":false})
            } else {
                track["Audio"]["Verified"] = true
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
            await request({"intent":"redownload", "album_id":album_id, "track_num":track["Track Number"], "url":url});
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


async function load() {
    let response_raw = await fetch("playlists/liked.csv");
    let response_text = await response_raw.text();
    let playlist = response_text.split(",");

    for (let id_pair of playlist) {
        console.log(id_pair)
        let id_pair_seperate = id_pair.split("_");
        let album_id = parseInt(id_pair_seperate[0]);
        let track_number = parseInt(id_pair_seperate[1]);

        add_track_card(album_id, track_number)
    }
}


load();