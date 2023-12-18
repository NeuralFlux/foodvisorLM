//--------------------
// GET USER MEDIA CODE
//--------------------
navigator.getUserMedia = ( navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia);

var video;
var webcamStream;

function startWebcam() {
    if (navigator.getUserMedia) {
        navigator.getUserMedia (
            // constraints
            {
                video: true,
                audio: false
            },

            // successCallback
            function(localMediaStream) {
                video = document.querySelector('video');
                video.srcObject=localMediaStream;
                webcamStream = localMediaStream;
            },

            // errorCallback
            function(err) {
                console.log("The following error occured: " + err);
            }
        );
    } else {
        console.log("getUserMedia not supported");
    }  
}

function stopWebcam() {
    webcamStream.getTracks().forEach(function(track) {
        track.stop();
    });
}
//---------------------
// TAKE A SNAPSHOT CODE
//---------------------
var canvas, ctx;

function init() {
    // Get the canvas and obtain a context for
    // drawing in it
    canvas = document.getElementById("myCanvas");
    ctx = canvas.getContext('2d');
}

function snapshot() {
    // Draws current image from the video element into the canvas
    ctx.drawImage(video, 0,0, canvas.width, canvas.height);
}