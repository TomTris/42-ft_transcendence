document.addEventListener("DOMContentLoaded", function() {
    
    var playButton1P = document.getElementById("Playbutton1P");
    var playButton2P = document.getElementById("Playbutton2P");
    var playButtonMP = document.getElementById("PlaybuttonMP");
    var textArea = document.getElementById("ta6");

    playButton1P.addEventListener("click", function() {
        alert("1 Player mode selected");
    });

    playButton2P.addEventListener("click", function() {
        alert("2 Player mode selected");
    });

    playButtonMP.addEventListener("click", function() {
        alert("Multi Player mode selected");
    });

    // more Event-Listener or Functions here
});
