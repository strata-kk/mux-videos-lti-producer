function activateNavTab(elementId) {
    let elt = document.getElementById(elementId);
    if (elt) {
        elt.setAttribute("aria-current", "page");
        elt.classList.add("active");
    }
}

(function (d) {
    // Auto-load all videos
    document.querySelectorAll('video').forEach(video => {
        videojs(video, { "fluid": true, "preload": "metadata" }).ready(function () {
            // https://www.npmjs.com/package/videojs-hotkeys
            this.hotkeys({
                volumeStep: 0.1,
                seekStep: 5,
                enableMute: true,
                enableFullscreen: true,
                enableNumbers: false,
                enableVolumeScroll: true,
                enableHoverScroll: true,
            })
        });
    })
})(document);
