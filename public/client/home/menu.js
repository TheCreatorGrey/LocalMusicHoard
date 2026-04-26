function open_menu(title) {
    bg = document.createElement("div");
    bg.style.backgroundColor = "rgba(0, 0, 0, 0.5)";
    bg.style.position = "absolute";
    bg.style.width = "100%";
    bg.style.height = "100%";
    bg.id = "menu_bg";
    document.getElementById("main_column").appendChild(bg);

    menu = document.createElement("div");
    menu.style.backgroundColor = "rgb(5, 5, 5)";
    menu.style.position = "absolute";
    menu.style.width = "100%";
    menu.style.top = "50%";
    menu.style.transform = "translateY(-50%)";
    menu.style.borderTop = "1px solid rgb(64, 64, 64)";
    menu.style.borderBottom = "1px solid rgb(64, 64, 64)";
    menu.style.textAlign = "center";
    menu.style.paddingTop = "25px";
    menu.style.paddingBottom = "25px";
    bg.appendChild(menu);

    header_text = document.createElement("h2");
    header_text.innerText = title;
    header_text.style.marginTop = "0";
    menu.appendChild(header_text);

    content = document.createElement("div");
    menu.appendChild(content);

    close_btn = document.createElement("button");
    close_btn.innerText = "Close";
    close_btn.style.backgroundColor = "rgb(200, 0, 100)";
    close_btn.style.color = "white";
    close_btn.style.width = "200px";
    close_btn.style.border = "none";
    close_btn.style.marginTop = "30px";
    close_btn.style.cursor = "pointer";
    menu.appendChild(close_btn);

    close_btn.onclick = () => {
        bg.remove();
    }

    return content;
}

//let shart = open_menu("Configure Track");




function track_config_menu(album_id, track_number) {
    let config_menu = open_menu("Album and Track Configuration");


    let label = document.createElement("div");
    label.innerText = "Name:";
    config_menu.appendChild(label);

    let name_textarea = document.createElement("textarea");
    config_menu.appendChild(name_textarea);

    name_textarea.onchange = () => {
        request({"intent":"set_name", "album_id":album_id, "track_num":track_number, "name":name_textarea.value});        
    }


    label = document.createElement("div");
    label.innerText = "Artists: (Separate by commas)";
    config_menu.appendChild(label);

    let artists_textarea = document.createElement("textarea");
    config_menu.appendChild(artists_textarea);

    artists_textarea.onchange = () => {
        request({"intent":"set_artists", "album_id":album_id, "track_num":track_number, "artists":artists_textarea.value});        
    }


    label = document.createElement("div");
    label.innerText = "Automatic audio download:";
    config_menu.appendChild(label);

    let url_textarea = document.createElement("textarea");
    config_menu.appendChild(url_textarea);

    let button_container = document.createElement("div");
    config_menu.appendChild(button_container);

    let find_url_btn = document.createElement("button");
    find_url_btn.innerText = "Search for URL";
    button_container.appendChild(find_url_btn);

    let auto_dl_btn = document.createElement("button");
    auto_dl_btn.innerText = "Download";
    button_container.appendChild(auto_dl_btn);

    find_url_btn.onclick = async () => {
        indicateLoading();
        let url = await request({"intent":"yt_search_track", "album_id":album_id, "track_num":track_number});
        url_textarea.innerText = url;
        finishLoading();
    }

    auto_dl_btn.onclick = async () => {
        indicateLoading();
        await request({"intent":"yt_dl_by_url", "album_id":album_id, "track_num":track_number, "url":url_textarea.value});
        finishLoading();
    }


    label = document.createElement("div");
    label.innerText = "\nAudio file:";
    config_menu.appendChild(label);

    let audio_input = document.createElement("input");
    audio_input.type = "file";
    audio_input.accept = ".mp3,.m4a,.wav,.flac,.ogg";
    config_menu.appendChild(audio_input);

    audio_input.onchange = () => {
        indicateLoading();

        file = audio_input.files[0];

        const reader = new FileReader();
        reader.onload = async function(e) {
            let file_type = "." + file.name.split(".").slice(-1)[0];

            const contents = e.target.result;

            await request({"intent":"set_audio", "album_id":album_id, "track_num":track_number, "file_type":file_type, "data_url":contents});
            finishLoading();
        };
        reader.readAsDataURL(file);
    }

    label = document.createElement("div");
    label.innerText = "\n640x640 Cover file:";
    config_menu.appendChild(label);

    label = document.createElement("div");
    label.innerText = "(applies to all tracks from the same release)";
    label.style.color = "grey";
    label.style.fontSize = "10px";
    config_menu.appendChild(label);

    let cover_display = document.createElement("canvas");
    cover_display.width = 640; // Resolution in pixels
    cover_display.height = 640;
    cover_display.style.width = "200px"; // Display size
    cover_display.style.height = "200px";
    cover_display.style.border = "1px solid white";
    config_menu.appendChild(cover_display)
    let display_ctx = cover_display.getContext("2d")

    config_menu.appendChild(document.createElement("br"));

    let cover_input = document.createElement("input");
    cover_input.type = "file";
    cover_input.accept = ".jpeg";
    config_menu.appendChild(cover_input);

    async function displayCover(source) {
        indicateLoading();

        let img = new Image();
        img.src = source;
        await img.decode();
        
        display_ctx.drawImage(img, 0, 0, 640, 640)

        finishLoading();
    }

    displayCover(`/covers/${album_id}.jpeg`)

    cover_input.onchange = () => {

        file = cover_input.files[0];

        const reader = new FileReader();
        reader.onload = async function(e) {
            const contents = e.target.result;

            displayCover(contents)

            await request({"intent":"set_cover", "album_id":album_id, "data_url":contents});
            finishLoading();
        };

        reader.readAsDataURL(file);
    }
}


async function album_cover_menu(album_id) {
    let album = await request({"intent":"get_album_info_from_id", "id":album_id});

    let menu = open_menu(`${album.Name} (${album["Release Year"]})`);

    let enlarged_cover = document.createElement("img");
    enlarged_cover.src = `/covers/${album.ID}.jpeg`
    enlarged_cover.style.width = "400px";
    enlarged_cover.style.height = "400px";
    menu.appendChild(enlarged_cover);
}


async function random_menu(album_id) {
    let menu = open_menu(`Play random track`);

    let random_downloaded_btn = document.createElement("button");
    random_downloaded_btn.innerText = "From all downloaded tracks";
    menu.appendChild(random_downloaded_btn);

    random_downloaded_btn.onclick = async () => {
        indicateLoading();
        await request({"intent":"yt_dl_by_url", "album_id":album_id, "track_num":track_number, "url":url_textarea.value});
        finishLoading();
    }
}


function new_playlist_menu() {
    let menu = open_menu("Create Playlist");

    let name_textarea = document.createElement("textarea")
    menu.appendChild(name_textarea)

    let create_button = document.createElement("button")
    create_button.innerText = "Create playlist"
    menu.appendChild(create_button)
}


function new_album_menu() {
    let reg_menu = open_menu("Album Registry");

    let label = document.createElement("div");
    label.innerText = "Name:";
    reg_menu.appendChild(label);

    let name_textarea = document.createElement("textarea");
    reg_menu.appendChild(name_textarea);


    label = document.createElement("div");
    label.innerText = "Type: (Album, Single, EP, Compilation)";
    reg_menu.appendChild(label);

    let type_textarea = document.createElement("textarea");
    reg_menu.appendChild(type_textarea);


    label = document.createElement("div");
    label.innerText = "Year:";
    reg_menu.appendChild(label);

    let year_textarea = document.createElement("textarea");
    reg_menu.appendChild(year_textarea);


    label = document.createElement("div");
    label.innerText = "Number of tracks:";
    reg_menu.appendChild(label);

    let num_tracks_textarea = document.createElement("textarea");
    reg_menu.appendChild(num_tracks_textarea);


    let button_container = document.createElement("div");
    reg_menu.appendChild(button_container);

    let add_btn = document.createElement("button");
    add_btn.innerText = "Create empty release registration";
    button_container.appendChild(add_btn);

    add_btn.onclick = async () => {
        let new_album_id = await request({"intent":"new_index", "name":name_textarea.value, "type":type_textarea.value, "track_count":parseInt(num_tracks_textarea.value), "year":year_textarea.value})
        load_album_page(new_album_id)
    }
}


function welcome_menu() {
    let menu = open_menu("Welcome to LMH");

    let text = document.createElement("span");
    text.innerText = 
    `This is a tool for downloading and streaming 
    music locally. To start loading tracks into your 
    library, you need to add indices. For now, 
    indexing needs to be done with a script, but 
    the user-friendly way will be added later.
    When a release is indexed, information on it
    such as the name, release year, tracks and
    album cover will be saved making them accessible
    and visible on the page. Tracks will not
    have audio immediately after indexing, meaning
    they can show up on the page but may not have
    audio. To download audio for a track, hover
    over the track and click the wrench. This will
    open the configuration menu where there will
    be further instructions.`;
    menu.appendChild(text);
}

welcome_menu();