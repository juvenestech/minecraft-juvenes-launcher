// Load
window.addEventListener("load", ()=>{
    eel.auth();
    document.getElementById('logo').addEventListener("click", ()=>{
        eel.startMinecraft();
    })
})

// Prevent Resize
window.addEventListener("resize", ()=>{
    window.resizeTo(415, 250);
});

// Set CODICE
eel.expose(setCode);
function setCode(text){
    document.getElementById('codice').innerHTML = text
}

// Set MESSAGE
eel.expose(setMessage);
function setMessage(text){
    document.getElementById('message').innerHTML = text
}

// Set PROGRESS
eel.expose(setProgress);
function setProgress(percentage){
    document.getElementById('progressbar').style.width = percentage+'%'
}
eel.expose(setProgressSpeed);
function setProgressSpeed(milliseconds){
    document.getElementById('progressbar').style.transition = milliseconds+'ms linear'
}
eel.expose(setProgressError);
function setProgressError(bool){
    document.getElementById('progressbar').style.backgroundColor = bool?'#EE1846':'#4EB6DF';
}

