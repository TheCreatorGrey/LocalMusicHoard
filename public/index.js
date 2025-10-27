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


let currently_playing_album_id = 0;
let currently_playing_track_number = 0;
async function play(album_id, track_number, play_next=true) {
    currently_playing_album_id = album_id
    currently_playing_track_number = track_number
    console.log(currently_playing_album_id)

    let info = await request({"intent":"get_track_info_from_id", "album_id":album_id, "track_num":track_number});
    audio_source.src = info.audio_url;
    audio_controls.load();
    audio_controls.play();

    album_cover.src = info.album_cover_url;
    icon.href = info.album_cover_url;

    let title = `${info.name} - ${info.artists[0]}`;
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

async function load() {
    let index = await request({"intent":"get_indices"});

    for (let album_id in index) {
        let album = index[album_id];
        
        let container = document.createElement("div");
        container.className = "album";
        content_area.appendChild(container);

        let header_text = document.createElement("h2");
        header_text.innerText = `${album.ID}: ${album.Name} (${album["Release Year"]})`;
        header_text.className = "header_text";
        container.appendChild(header_text);


        let album_dl_btn = document.createElement("img");
        album_dl_btn.className = "inline_button"
        album_dl_btn.src = "./assets/download_from_search.svg";
        album_dl_btn.title = "Automatically download audio for all tracks in this album by searching";
        header_text.appendChild(album_dl_btn);

        album_dl_btn.onclick = async () => {
            await request({"intent":"dl_by_search_album", "album_id":album["ID"]});
        }


        let contributing_artists = [];
        let artist_text = document.createElement("div");
        container.appendChild(artist_text);

        let cover = document.createElement("img");
        cover.src = `covers/${album["ID"]}.jpeg`;
        cover.className = "cover"
        container.appendChild(cover);


        for (let track of album.Tracks) {
            let track_container = document.createElement("div");
            track_container.className = "track_container"

            let play_btn = document.createElement("img");
            play_btn.className = "inline_button"
            play_btn.src = "./assets/play.svg";
            track_container.appendChild(play_btn);

            let track_text = document.createElement("span");
            track_text.innerText = track.Name;
            track_container.appendChild(track_text);

            for (let artist of track.Artists) {
                if (! contributing_artists.includes(artist)) {
                    contributing_artists.push(artist);
                }
            }

            // Adding a function to the event like () => {} instead of function () captures the variable values at the time it is assigned
            play_btn.onclick = async () => {
                play(album["ID"], track["Track Number"])
            }

            let verify_btn = document.createElement("img");
            verify_btn.className = "inline_button"
            verify_btn.src = "./assets/unverified.svg";
            verify_btn.title = "Verify that the audio for this track is correct";
            track_container.appendChild(verify_btn);

            verify_btn.onclick = () => {
                if (!track["Audio"]) {
                    track["Audio"] = {Verified: false}
                }

                if (track["Audio"]["Verified"]) {
                    track["Audio"]["Verified"] = false
                    verify_btn.src = "./assets/unverified.svg"
                    request({"intent":"set_verification", "album_id":album["ID"], "track_num":track["Track Number"], "bool":false})
                } else {
                    track["Audio"]["Verified"] = true
                    verify_btn.src = "./assets/verified.svg"
                    request({"intent":"set_verification", "album_id":album["ID"], "track_num":track["Track Number"], "bool":true})
                }
                
            }



            let dl_from_url_btn = document.createElement("img");
            dl_from_url_btn.className = "inline_button"
            dl_from_url_btn.src = "./assets/download_from_link.svg";
            dl_from_url_btn.title = "Automatically download audio for this track from pasted URL";
            track_container.appendChild(dl_from_url_btn);

            dl_from_url_btn.onclick = () => {
                let url = document.getElementById("url_box").value;
                console.log(url);
                request({"intent":"redownload", "album_id":album["ID"], "track_num":track["Track Number"], "url":url})
            }


            let track_dl_bysearch_btn = document.createElement("img");
            track_dl_bysearch_btn.className = "inline_button"
            track_dl_bysearch_btn.src = "./assets/download_from_search.svg";
            track_dl_bysearch_btn.title = "Automatically download audio for this track by searching";
            track_container.appendChild(track_dl_bysearch_btn);
    
            track_dl_bysearch_btn.onclick = async () => {
                await request({"intent":"dl_by_search", "album_id":album["ID"], "track_num":track["Track Number"]});
            }


            container.appendChild(track_container);
        }

        artist_text.innerText = contributing_artists.join(", ")
    }
}

//load()