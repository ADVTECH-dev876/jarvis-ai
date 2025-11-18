@app.get("/", response_class=HTMLResponse)
async def ui():
    return """
    <html>
    <head><title>JARVIS</title></head>
    <body style="font-family: sans-serif; padding: 20px;">
        <h2>🎙️ JARVIS Assistant</h2>
        <button onclick="startListening()" style="font-size: 18px; padding: 10px;">Speak to JARVIS</button>
        <div id="transcript" style="margin-top: 20px; color: #555;"></div>
        <audio id="audioPlayer" autoplay></audio>

        <script>
            async function startListening() {
                document.getElementById('transcript').innerText = "Listening...";
                const res = await fetch('/voice');
                const data = await res.json();
                document.getElementById('transcript').innerText = "JARVIS: " + data.response;
                
                // Play TTS
                const audio = document.getElementById('audioPlayer');
                audio.src = "/speak?text=" + encodeURIComponent(data.response);
                audio.play();
            }
        </script>
    </body>
    </html>
    """
