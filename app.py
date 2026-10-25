import os, random, string
from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-before-production")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

QUESTIONS = [
    {"q":"What is the basic unit of heredity?", "options":["Nucleotide","Gene","Chromosome","Protein"], "answer":1, "topic":"Genetics", "explain":"A gene is a DNA sequence that contributes to a functional product or trait."},
    {"q":"Which molecule carries genetic instructions in most living organisms?", "options":["DNA","Glucose","Lipids","Cellulose"], "answer":0, "topic":"Genomics", "explain":"DNA stores hereditary information in its nucleotide sequence."},
    {"q":"Which process makes an RNA copy from a DNA template?", "options":["Replication","Transcription","Translation","Mutation"], "answer":1, "topic":"Molecular biology", "explain":"During transcription, RNA polymerase uses DNA as a template to synthesize RNA."},
    {"q":"Where does translation usually occur in a cell?", "options":["Ribosome","Nucleus only","Golgi apparatus","Lysosome"], "answer":0, "topic":"Cell biology", "explain":"Ribosomes read mRNA and assemble amino acids into a protein."},
    {"q":"What are the four common DNA bases?", "options":["A, C, G, T","A, C, G, U","A, T, U, X","C, G, U, P"], "answer":0, "topic":"Genetics", "explain":"DNA contains adenine, cytosine, guanine and thymine."},
    {"q":"A change in the DNA sequence is called a…", "options":["Codon","Mutation","Ribosome","Phenotype"], "answer":1, "topic":"Genomics", "explain":"A mutation is a change in genetic sequence; its effects can vary."},
    {"q":"Which base pairs with adenine in DNA?", "options":["Cytosine","Guanine","Thymine","Uracil"], "answer":2, "topic":"Genetics", "explain":"In DNA, adenine pairs with thymine; cytosine pairs with guanine."},
    {"q":"What does CRISPR-Cas9 help scientists do?", "options":["Edit targeted DNA sequences","Measure blood pressure","Make all proteins glow","Replace every chromosome"], "answer":0, "topic":"Biotechnology", "explain":"CRISPR-Cas9 is a tool used to target and edit DNA at selected sites."},
    {"q":"Which units make up proteins?", "options":["Fatty acids","Amino acids","Nucleotides","Simple sugars"], "answer":1, "topic":"Biochemistry", "explain":"Proteins are polymers built from amino-acid subunits."},
    {"q":"What is a genome?", "options":["All of an organism's genetic material","One protein","A single cell membrane","A type of microscope"], "answer":0, "topic":"Genomics", "explain":"A genome is the complete set of genetic material in an organism."},
    {"q":"Which organelle contains most DNA in a human cell?", "options":["Nucleus","Ribosome","Golgi body","Cell wall"], "answer":0, "topic":"Cell biology", "explain":"Most human-cell DNA is housed in the nucleus, with a small amount in mitochondria."},
    {"q":"What is the role of mRNA?", "options":["Carry a message from DNA to ribosomes","Store energy as fat","Digest waste","Build the cell membrane directly"], "answer":0, "topic":"Molecular biology", "explain":"Messenger RNA carries sequence information used by ribosomes during protein synthesis."}
]

rooms = {}

def make_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("create_room")
def create_room(data):
    name = (data.get("name") or "Player").strip()[:18]
    code = make_code()
    while code in rooms:
        code = make_code()
    rooms[code] = {"players": {}, "scores": {}, "round": 0, "question": None, "answered": set(), "active": False, "used": []}
    join_room(code)
    rooms[code]["players"][request.sid] = name
    rooms[code]["scores"][request.sid] = 0
    emit("room_joined", {"code":code, "name":name, "host":True})
    broadcast_players(code)

@socketio.on("join_room")
def join_existing(data):
    code = (data.get("code") or "").strip().upper()
    name = (data.get("name") or "Player").strip()[:18]
    if code not in rooms:
        emit("error_message", {"message":"Room not found. Check the code or create a new room."})
        return
    if rooms[code]["active"]:
        emit("error_message", {"message":"This game has already started. Create a new room for another match."})
        return
    join_room(code)
    rooms[code]["players"][request.sid] = name
    rooms[code]["scores"][request.sid] = 0
    emit("room_joined", {"code":code, "name":name, "host":False})
    broadcast_players(code)

def broadcast_players(code):
    if code in rooms:
        r = rooms[code]
        socketio.emit("players_update", {
            "players":[{"name":n, "score":r["scores"].get(sid,0)} for sid,n in r["players"].items()],
            "count":len(r["players"])
        }, to=code)

def send_question(code):
    r = rooms[code]
    if r["round"] >= 8:
        r["active"] = False
        board = sorted([{"name":n,"score":r["scores"].get(sid,0)} for sid,n in r["players"].items()], key=lambda x:x["score"], reverse=True)
        socketio.emit("game_over", {"board":board}, to=code)
        return
    available = [i for i in range(len(QUESTIONS)) if i not in r["used"]]
    if not available:
        r["used"] = []
        available = list(range(len(QUESTIONS)))
    idx = random.choice(available)
    r["used"].append(idx)
    q = QUESTIONS[idx]
    r["round"] += 1
    r["question"] = q
    r["answered"] = set()
    socketio.emit("new_question", {
        "round":r["round"], "total":8, "q":q["q"], "options":q["options"],
        "topic":q["topic"], "time":20
    }, to=code)
    socketio.start_background_task(question_timer, code, r["round"])

def question_timer(code, round_num):
    socketio.sleep(20)
    if code not in rooms:
        return
    r = rooms[code]
    if r["active"] and r["round"] == round_num:
        socketio.emit("question_timeout", {}, to=code)
        socketio.sleep(2)
        if r["active"] and r["round"] == round_num:
            send_question(code)

@socketio.on("start_game")
def start_game(data):
    code = (data.get("code") or "").upper()
    if code not in rooms or request.sid not in rooms[code]["players"]:
        return
    r = rooms[code]
    if len(r["players"]) < 1:
        return
    r["active"] = True
    r["round"] = 0
    r["used"] = []
    r["answered"] = set()
    for sid in r["scores"]:
        r["scores"][sid] = 0
    broadcast_players(code)
    send_question(code)

@socketio.on("submit_answer")
def submit_answer(data):
    code = (data.get("code") or "").upper()
    if code not in rooms:
        return
    r = rooms[code]
    if not r["active"] or request.sid not in r["players"] or request.sid in r["answered"]:
        return
    r["answered"].add(request.sid)
    q = r["question"]
    correct = int(data.get("answer", -1)) == q["answer"]
    points = 100 if correct else 0
    if correct:
        r["scores"][request.sid] = r["scores"].get(request.sid,0) + points
    emit("answer_result", {"correct":correct, "points":points, "explain":q["explain"], "answer":q["answer"]})
    broadcast_players(code)
    if len(r["answered"]) >= len(r["players"]):
        socketio.sleep(2)
        if r["active"]:
            send_question(code)

@socketio.on("disconnect")
def disconnect():
    for code in list(rooms.keys()):
        r = rooms[code]
        if request.sid in r["players"]:
            del r["players"][request.sid]
            r["scores"].pop(request.sid, None)
            if not r["players"]:
                del rooms[code]
            else:
                broadcast_players(code)
            break

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), allow_unsafe_werkzeug=True)
