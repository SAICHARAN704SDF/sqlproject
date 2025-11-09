from flask import Flask, render_template, request, jsonify, session
import pickle, os, random, json
from collections import defaultdict
from db import get_conn
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from datetime import datetime

app = Flask(__name__)
app.secret_key = "escapestress_secret_2025"

# ==========================================
# 1️⃣ Ensure DB Exists
# ==========================================
DB_PATH = "stress_chat.db"
if not os.path.exists(DB_PATH):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY, user TEXT, bot TEXT, label TEXT)")
        conn.commit()
    finally:
        conn.close()


def ensure_db_schema():
    conn = get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA table_info(chats)")
            cols = [r[1] for r in cur.fetchall()]
        except Exception:
            cols = []
        if 'label' not in cols:
            cur.execute("ALTER TABLE chats ADD COLUMN label TEXT")
            conn.commit()
        # Ensure journals, users, resources and actions tables exist (safe no-op if db_setup.py already created them)
        try:
            cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT)")
            cur.execute("CREATE TABLE IF NOT EXISTS journals (id INTEGER PRIMARY KEY AUTOINCREMENT, entry TEXT, created_at TEXT)")
            cur.execute("CREATE TABLE IF NOT EXISTS resources (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT, category TEXT)")
            cur.execute("CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY AUTOINCREMENT, action_type TEXT, details TEXT, created_at TEXT)")
            conn.commit()
        except Exception:
            # Some DB backends may raise different errors — ignore here
            pass
    finally:
        conn.close()

ensure_db_schema()

# ==========================================
# 2️⃣ Load ML Model
# ==========================================
MODEL_PATH = os.path.join("model", "emotion_model.pkl")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run train_model.py first.")

vectorizer, model = pickle.load(open(MODEL_PATH, "rb"))

# ==========================================
# 3️⃣ Knowledge Base Loader
# ==========================================
KB_PATH = os.path.join(os.path.dirname(__file__), 'knowledge.json')
if os.path.exists(KB_PATH):
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        kb = json.load(f)
else:
    kb = []

# ==========================================
# 4️⃣ Stress Type & Intent Detection
# ==========================================
def detect_stress_type(text):
    t = text.lower()
    mapping = [
        ("Anxiety", ["anxious", "panic", "worry", "nervous"]),
        ("Depression", ["hopeless", "sad", "empty", "alone"]),
        ("Work/Academic", ["work", "exam", "study", "deadline", "project", "college"]),
        ("Burnout", ["tired", "exhaust", "overwhelm"]),
        ("Relationship", ["partner", "friend", "breakup", "love"]),
    ]
    for label, kws in mapping:
        if any(kw in t for kw in kws):
            return label
    return "General Stress"


def detect_intent(text):
    t = text.lower()
    intents = {
        'workload': ['work', 'exam', 'deadline', 'project', 'study', 'assignment'],
        'sleep': ['sleep', 'tired', 'rest', 'insomnia'],
        'panic': ['panic', 'hypervent', 'shortness of breath'],
        'relationship': ['partner', 'relationship', 'friend', 'breakup'],
        'suicidal': ['suicide', 'kill myself', 'worthless', 'end my life']
    }
    for intent, kws in intents.items():
        if any(kw in t for kw in kws):
            return intent
    return 'general'


def is_mental_health_query(text):
    t = text.lower()
    keywords = [
        'stress', 'depress', 'anxious', 'tired', 'sad', 'panic', 'lonely',
        'hopeless', 'burnout', 'overwhelm', 'fear', 'sleep', 'mental', 'worry'
    ]
    if any(kw in t for kw in keywords):
        return True
    if detect_intent(text) != 'general':
        return True
    if detect_stress_type(text) != 'General Stress':
        return True
    return False

# ==========================================
# 5️⃣ Random Dynamic Reply Generator
# ==========================================
def dynamic_reply(pred, stress_type, intent):
    responses = {
        "High Stress": [
            "That sounds really intense 😞. You’ve been carrying a lot — maybe try a slow breathing exercise?",
            "It’s okay to pause and breathe. You’re not alone in this 💙.",
            "Sounds like too much pressure right now. Want to try a short mental reset?",
            "That must be overwhelming. Take 3 slow breaths and give your body a moment to calm down.",
            "I know it feels like too much. What’s the biggest thing stressing you right now?"
        ],
        "Medium Stress": [
            "You’re under pressure, but still grounded. Let’s slow things down a bit.",
            "Seems like you’re holding up fine — want to try a relaxation tip?",
            "You’ve got a lot going on. Try one small self-care action right now.",
            "Your stress sounds manageable — still, a short walk could help clear your head.",
            "You’re doing better than you think. Keep breathing through it."
        ],
        "Low Stress": [
            "Good to hear you’re calm 🌿. Let’s keep that balance going.",
            "That’s great — stay in this peaceful headspace as long as you can.",
            "You sound centered and relaxed. Maybe enjoy a quick mindful moment.",
            "You’re in control — that’s great energy to maintain.",
            "Keep protecting this calm — it’s precious."
        ],
        "Work/Academic": [
            "Deadlines can be rough. Try focusing on one task for 25 minutes — Pomodoro style.",
            "Work pressure builds up — short breaks actually boost focus.",
            "You sound mentally drained. Let’s reset — step away for 5 minutes.",
            "Overthinking assignments burns energy. Focus on what’s achievable today.",
            "You’re capable of handling this, just one thing at a time."
        ],
        "Relationship": [
            "That’s emotionally heavy 💔. It’s okay to take time for yourself.",
            "Relationships get messy — but your mental peace comes first.",
            "Feeling disconnected hurts. Try writing what you wish you could say — it helps release pain.",
            "You deserve understanding and comfort, not confusion.",
            "Even loneliness passes — you’re stronger than you think."
        ],
        "Calm/Positive": [
            "That’s wonderful 😌. Keep that relaxed energy flowing.",
            "You seem in a good place. Maybe play some calm music to stay grounded.",
            "Peace looks good on you — keep nurturing it.",
            "Grateful moments like these are worth holding onto.",
            "Nice! Keep enjoying this positive state today."
        ],
        "General Stress": [
            "It’s okay to feel stressed. Let’s take a deep breath first.",
            "We all have heavy days. What’s one thing you can let go of right now?",
            "Let’s focus on small relief — breathing, stretching, music, or journaling?",
            "Stress happens, but you don’t have to face it alone.",
            "Want me to guide a quick relaxation technique?"
        ]
    }
    msg = random.choice(responses.get(pred, responses["General Stress"]))
    msg += random.choice(["", " Remember, small breaks help big stress.", " You’re doing your best — that’s enough."])
    return msg


# ==========================================
# 6️⃣ Main Chat Analysis
# ==========================================
def analyze_emotion_structured(user_input):
    X = vectorizer.transform([user_input])
    pred = model.predict(X)[0]

    # confidence/probabilities if available
    confidence = {}
    try:
        probs = model.predict_proba(X)[0]
        classes = model.classes_
        confidence = {str(c): float(p) for c, p in zip(classes, probs)}
    except Exception:
        confidence = {}

    stress_type = detect_stress_type(user_input)
    intent = detect_intent(user_input)
    message = dynamic_reply(pred, stress_type, intent)

    # generate tips and short action plan
    def coping_tips_for(kind):
        tips_map = {
            'Anxiety': [
                'Try a 4-4-4 breathing: inhale 4s, hold 4s, exhale 4s.',
                'Grounding: name 5 things you see, 4 things you can touch.',
                'If worry is future-focused, schedule a 10-minute "worry time" later.'
            ],
            'Depression': [
                'Try behavioral activation: one small achievable task (e.g., 5-minute walk).',
                'Connect with a supportive person or write one sentence about how you feel.'
            ],
            'Work/Academic': [
                'Break tasks into 25-minute focus blocks (Pomodoro).',
                'Prioritize 1–2 tasks for today and let others wait.'
            ],
            'Burnout': [
                'Schedule a real rest: an afternoon without work tasks.',
                'Say no to one request this week to protect energy.'
            ],
            'Relationship': [
                'Try writing what you need to say before a conversation.',
                'Set a small, specific boundary and observe what changes.'
            ],
            'General Stress': [
                'Take three slow diaphragmatic breaths.',
                'Step outside for 5 minutes and notice your surroundings.'
            ]
        }
        return tips_map.get(kind, tips_map['General Stress'])

    def generate_action_plan(kind, intent_text, user_text):
        plan = []
        if kind == 'Anxiety' or intent_text == 'panic':
            plan = [
                'Pause and do a 3-minute breathing exercise (4-4-4).',
                'Ground: name 5 things you see, 4 you can touch, 3 you hear.',
                'If it continues, consider contacting a trusted person or professional.'
            ]
        elif kind == 'Work/Academic' or intent_text == 'workload':
            plan = [
                'Identify the single most important task and work on it for 25 minutes.',
                'Take a 10-minute break and move your body.',
                'Re-evaluate deadlines and ask for help if needed.'
            ]
        else:
            plan = [
                'Take 3 slow diaphragmatic breaths to reset.',
                'Write down the top worry in one sentence.',
                'Choose one small action you can do in the next 30 minutes.'
            ]
        return plan

    def get_resources_for(kind):
        conn = get_conn()
        try:
            cur = conn.cursor()
            try:
                cur.execute("SELECT title, url, category FROM resources WHERE category=? OR category='general' ORDER BY id ASC LIMIT 5", (kind,))
                rows = cur.fetchall()
            except Exception:
                # pymysql dict cursor or different param style
                cur.execute("SELECT title, url, category FROM resources WHERE category=%s OR category='general' ORDER BY id ASC LIMIT 5", (kind,))
                rows = cur.fetchall()
        finally:
            conn.close()
        out = []
        for r in rows:
            if isinstance(r, dict):
                out.append({"title": r.get('title'), "url": r.get('url'), "category": r.get('category')})
            else:
                out.append({"title": r[0], "url": r[1], "category": r[2]})
        return out

    tips = coping_tips_for(stress_type)
    action_plan = generate_action_plan(stress_type, intent, user_input)
    resources = get_resources_for(stress_type)

    # DB Logging
    conn = get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO chats (user, bot, label) VALUES (?, ?, ?)", (user_input, message, pred))
            conn.commit()
        except Exception:
            cur.execute("INSERT INTO chats (user, bot, label) VALUES (%s, %s, %s)", (user_input, message, pred))
            conn.commit()
    finally:
        conn.close()

    guide = None
    if stress_type == 'Anxiety' or intent == 'panic':
        guide = {'type': 'breathing', 'instruction': 'Try 4-4-4 breathing: inhale 4s, hold 4s, exhale 4s for 4 cycles.'}

    return {
        "label": str(pred),
        "message": message,
        "stress_type": stress_type,
        "intent": intent,
        "confidence": confidence,
        "tips": tips,
        "action_plan": action_plan,
        "resources": resources,
        "guide": guide
    }

# ==========================================
# 7️⃣ Routes
# ==========================================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get", methods=["POST"])
def chat():
    msg = request.form.get("msg", "").strip()
    if not msg:
        return jsonify({"error": "Empty message"}), 400

    if not is_mental_health_query(msg):
        return jsonify({
            "label": "OutOfScope",
            "message": "Let’s focus on how you’re feeling or what’s stressing you today 💬."
        })

    analysis = analyze_emotion_structured(msg)
    return jsonify(analysis)


@app.route("/history")
def history():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user, bot, label FROM chats ORDER BY id DESC LIMIT 50")
        rows = cur.fetchall()
    finally:
        conn.close()

    data = []
    for r in rows:
        if isinstance(r, dict):
            data.append({"user": r.get('user'), "bot": r.get('bot'), "label": r.get('label')})
        else:
            data.append({"user": r[0], "bot": r[1], "label": r[2]})
    return jsonify(data)


# ------------------------------------------
# Lightweight endpoints used by the frontend
# ------------------------------------------


@app.route('/resources_db')
def resources_db():
    conn = get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, title, url, category FROM resources ORDER BY id ASC")
            rows = cur.fetchall()
        except Exception:
            cur.execute("SELECT id, title, url, category FROM resources ORDER BY id ASC")
            rows = cur.fetchall()
    finally:
        conn.close()

    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append({"id": r.get('id'), "title": r.get('title'), "url": r.get('url'), "category": r.get('category')})
        else:
            out.append({"id": r[0], "title": r[1], "url": r[2], "category": r[3]})
    return jsonify(out)


@app.route('/breathing')
def breathing():
    steps = [
        {"text": "Sit comfortably and place one hand on your belly."},
        {"text": "Inhale slowly for 4 seconds, feeling your belly rise."},
        {"text": "Hold gently for 4 seconds."},
        {"text": "Exhale slowly for 6 seconds, feeling your belly fall."},
        {"text": "Repeat this 4–6 times until you feel calmer."}
    ]
    return jsonify({"steps": steps})


@app.route('/journal', methods=['POST'])
def save_journal():
    entry = request.form.get('entry') or (request.get_json(silent=True) or {}).get('entry')
    if not entry:
        return jsonify({"error": "Empty entry"}), 400
    created_at = datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO journals (entry, created_at) VALUES (?, ?)", (entry, created_at))
            conn.commit()
        except Exception:
            cur.execute("INSERT INTO journals (entry, created_at) VALUES (%s, %s)", (entry, created_at))
            conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "ok", "created_at": created_at})


@app.route('/journal/recent')
def journal_recent():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT entry, created_at FROM journals ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
    finally:
        conn.close()
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append({"entry": r.get('entry'), "created_at": r.get('created_at')})
        else:
            out.append({"entry": r[0], "created_at": r[1]})
    return jsonify(out)


@app.route('/user', methods=['POST'])
def create_user():
    name = request.form.get('name') or ''
    email = request.form.get('email') or ''
    conn = get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
            conn.commit()
        except Exception:
            cur.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
            conn.commit()
    finally:
        conn.close()
    return jsonify({"name": name, "email": email})


@app.route('/knowledge')
def knowledge():
    return jsonify(kb)


@app.route('/log_action', methods=['POST'])
def log_action():
    action_type = request.form.get('action_type') or request.json.get('action_type') if request.get_json(silent=True) else None
    details = request.form.get('details') or request.json.get('details') if request.get_json(silent=True) else None
    created_at = datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO actions (action_type, details, created_at) VALUES (?, ?, ?)", (action_type, details, created_at))
            conn.commit()
        except Exception:
            cur.execute("INSERT INTO actions (action_type, details, created_at) VALUES (%s, %s, %s)", (action_type, details, created_at))
            conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "logged"})


if __name__ == "__main__":
    print("🚀 EscapeStress Chatbot starting...")
    app.run(debug=True, host="127.0.0.1", port=5000)
