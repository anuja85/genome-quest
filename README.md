# Genome Quest

A browser-based multiplayer science quiz for genetics, genomics, cell biology, and biotechnology. Players create a room, share its code, and compete in an eight-question live match.

## Features
- Real-time rooms with shareable five-character codes
- Live player list and score leaderboard
- Timed questions, instant feedback, explanations, and end-of-game results
- Responsive neon science-themed interface
- Runs without API keys or paid services

## Run locally
1. Install Python 3.10 or newer.
2. In this folder, run `python -m venv .venv`.
3. Activate the environment:
   - Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
   - macOS/Linux: `source .venv/bin/activate`
4. Run `pip install -r requirements.txt`.
5. Run `python app.py`.
6. Open `http://127.0.0.1:5000` in your browser. Open another browser/device on the same network only if it can reach the host machine.

## Deploy free on Render
1. Create a GitHub repository and upload these project files.
2. Sign in to Render and choose **New > Blueprint**.
3. Connect the repository containing `render.yaml`.
4. Deploy the service and wait for the public `onrender.com` URL.
5. Open the public URL in two browsers/devices, create a room, and join with the room code.

Free hosting may sleep when inactive; the first load can take a little while. Verify the public link and test a match before submitting to Handshake.

## Important notes
- This starter uses a built-in question bank; it does not call OpenAI or generate questions dynamically.
- This is an educational prototype, not a production-hardened service. Add moderation, rate limiting, stronger room lifecycle handling, and testing before a larger public launch.
- Do not claim the game uses OpenAI until you actually integrate and test an API key.
