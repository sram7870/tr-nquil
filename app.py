import os
import json
import logging
import urllib.parse
import matplotlib
import requests
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, jsonify, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash

matplotlib.use('Agg')

# --- CONFIG ---
SQLITE_DB_FILE = 'mental_health.db'
JOURNAL_DB_FILE = 'journal_db.json'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
UPLOAD_FOLDER = 'uploads'

OPENROUTER_API_KEY = os.getenv("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")
if not OPENROUTER_API_KEY:
    raise RuntimeError("Missing OPENROUTER_API_KEY environment variable")

# --- LOGGING ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger()

# --- FLASK APP ---
app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- DATABASE ---
def init_db():
    with sqlite3.connect(SQLITE_DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT,
                age INTEGER,
                goals TEXT,
                concerns TEXT
            )
        ''')
        conn.commit()

# --- GPT CALL ---
def call_openrouter_gpt(prompt, max_tokens=800):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        logger.exception("Error in GPT call: %s", e)
        return "Sorry, something went wrong while trying to respond. Please try again later."

# --- AUTH ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        form = request.form
        email = form['email']
        password = form['password']
        name = form.get('name', 'Guest')
        age = form.get('age')
        goals = form.get('goals')
        concerns = form.get('concerns')

        session['user_id'] = 1
        session['name'] = name
        session['email'] = email
        session['goals'] = goals
        session['concerns'] = concerns

        return redirect(url_for('ind'))

    return render_template("auth.html")

@app.route('/ind')
def ind():
    return render_template('index.html')

@app.route('/auth/logout')
def logout():
    session.clear()
    return redirect(url_for('auth'))

# --- CHATBOT ---
@app.route('/message', methods=['POST'])
def chatbot_message():
    data = request.json
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please enter a message so I can respond."})

    prompt = f"""
    You are a compassionate and empathetic mental health chatbot designed to offer emotional support and active listening. 
    A user has written the following message: "{user_message}". 
    Please respond gently, supportively, and constructively. Avoid giving any medical diagnoses. 
    Always respond in 1 - 2 paragraphs, not bullet points/lists.
    """

    bot_reply = call_openrouter_gpt(prompt, max_tokens=800)
    return jsonify({"reply": bot_reply})

# --- JSON JOURNAL DB ---
def load_db():
    if not os.path.exists(JOURNAL_DB_FILE):
        return {}
    with open(JOURNAL_DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    with open(JOURNAL_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except:
        return False

# --- JOURNAL API ---
@app.route("/api/journal/<date>", methods=["GET"])
def get_entry(date):
    if not validate_date(date):
        return abort(400, description="Invalid date format")
    db = load_db()
    entry = db.get(date)
    if not entry:
        return abort(404, description="Entry not found")
    return jsonify(entry)

@app.route("/api/journal/<date>", methods=["POST"])
def save_entry(date):
    if not validate_date(date):
        return abort(400, description="Invalid date format")
    data = request.json or {}
    required_fields = ["content", "mood", "tags", "habits", "goals"]
    for field in required_fields:
        if field not in data:
            return abort(400, description=f"Missing field: {field}")

    db = load_db()
    db[date] = {
        "content": data["content"],
        "mood": data["mood"],
        "tags": data["tags"],
        "habits": data["habits"],
        "goals": data["goals"]
    }
    save_db(db)
    return jsonify({"status": "saved", "date": date})

# --- SENTIMENT ANALYSIS ---
@app.route("/api/ai/sentiment", methods=["POST"])
def sentiment_analysis():
    data = request.json or {}
    text = data.get("text", "")
    if not text:
        return abort(400, description="Missing text for sentiment analysis")

    prompt = f"""
    Analyze the sentiment of the following journal entry. Respond in this format:
    Sentiment: Positive/Neutral/Negative
    Explanation: Brief explanation of the detected sentiment.

    Journal Entry:
    {text}
    """
    result = call_openrouter_gpt(prompt)
    return jsonify({"sentiment": result})

# --- MOOD TREND ---
@app.route("/api/analytics/moodtrend", methods=["GET"])
def mood_trend():
    days = request.args.get("days", "7")
    try:
        days = int(days)
    except:
        days = 7
    if days < 1 or days > 30:
        days = 7

    db = load_db()
    today = datetime.utcnow().date()
    trend = []
    valid_moods = {"happy","calm","neutral","sad","anxious","angry"}

    for i in range(days):
        d = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        entry = db.get(date_str)
        mood = entry.get("mood") if entry and entry.get("mood") in valid_moods else None
        trend.append({"date": date_str, "mood": mood})

    trend.reverse()
    return jsonify(trend)

# --- RUN ---
if __name__ == '__main__':
    if not os.path.exists(SQLITE_DB_FILE):
        print(f"Creating SQLite database {SQLITE_DB_FILE}...")
        init_db()
    app.run(debug=True)
