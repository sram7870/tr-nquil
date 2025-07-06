import json, logging, urllib.parse, matplotlib, os, requests, sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, session, abort

from werkzeug.security import generate_password_hash, check_password_hash

matplotlib.use('Agg')

# Statistic page scripts (not running/used)

# Logging config
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger()

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)

OPENROUTER_API_KEY = "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"
UPLOAD_FOLDER = 'uploads'
DB_FILE = 'mental_health.db'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
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

    except requests.exceptions.HTTPError as http_err:
        logger.exception("HTTP error: %s", http_err)
    except requests.exceptions.RequestException as req_err:
        logger.exception("Request error: %s", req_err)
    except json.JSONDecodeError as json_err:
        logger.exception("JSON decode error: %s", json_err)
    except Exception:
        logger.exception("General error in call_openrouter_gpt")

    return "Sorry, something went wrong while trying to respond. Please try again in a moment."

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

        # Simulate successful login/registration (no DB)
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

@app.route('/index', methods=['POST'])
def index():
    return render_template("index.html")

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

@app.route('/generate-art', methods=['POST'])
def generate_art():
    data = request.get_json()
    emotion = data.get("emotion", "").strip()

    if not emotion:
        return jsonify({"error": "Emotion input is required."}), 400

    prompt = f"""
    Convert the following emotional state into a visual art theme using abstract, metaphorical, or nature-based language. Avoid literal emotion words.
    Emotion: "{emotion}"
    Return a short phrase or keywords, like: "misty forest at dawn", "blue swirls and golden sparks", or "sunset behind a mountain".
    Just return a short keyword phrase suitable for visual search.
    """

    try:
        visual_keywords = call_openrouter_gpt(prompt, max_tokens=30)
        cleaned = visual_keywords.replace('"', '').replace(',', '').strip()
        keyword_query = urllib.parse.quote_plus(cleaned)
        image_url = f"https://source.unsplash.com/512x512/?{keyword_query}"
        print(image_url)

        return jsonify({
            "imageUrl": image_url,
            "prompt": visual_keywords
        })

    except Exception:
        logger.exception("Error generating visual art")
        return jsonify({"error": "Failed to generate visual."}), 500

cached_boost = {"date": None, "data": None}

@app.route('/daily-mental-boost', methods=['GET'])
def daily_mental_boost():
    force_refresh = request.args.get('refresh') == '1'
    today = datetime.utcnow().date()

    if not force_refresh and cached_boost["date"] == today:
        return jsonify(cached_boost["data"])

    try:
        prompts = {
            "prompt": "Give me a short self-reflection prompt for mental health today (1 sentence).",
            "quote": "Give me an uplifting quote about self-care or resilience.",
            "activities": "List exactly 3 short, encouraging activities to support mental health today. Each on its own line without numbering or bullets.",
            "tip": "Give me a practical mindfulness tip in 1-2 sentences, suitable for daily use.",
            "affirmation": (
                "Write a motivational affirmation in paragraph form (2–3 sentences). "
                "Make it sound warm, uplifting, and like a personal message of strength."
            )
        }

        results = {k: call_openrouter_gpt(v, max_tokens=80 if k == "affirmation" else 40) for k, v in prompts.items()}

        activity_list = [a.strip('-•–123. ').strip() for a in results["activities"].split('\n') if a.strip()][:3]

        data = {
            "prompt": results["prompt"],
            "quote": results["quote"],
            "activities": activity_list,
            "tip": results["tip"],
            "affirmation": results["affirmation"]
        }

        if not force_refresh:
            cached_boost["date"] = today
            cached_boost["data"] = data

        return jsonify(data)

    except Exception:
        logger.exception("Error generating daily mental boost")
        return jsonify({
            "prompt": "Reflect on one small thing that went well today.",
            "quote": "You’ve survived 100% of your worst days.",
            "activities": ["Breathe deeply for 1 minute", "Send a kind message to someone", "Write in your journal"],
            "tip": "Pause and focus on your breath. Inhale deeply, exhale slowly, and notice how your body feels.",
            "affirmation": (
                "You are growing stronger every day, even in the quiet moments. "
                "You’ve faced challenges with courage, and you are more resilient than you realize. "
                "Keep going—you are worthy of peace and purpose."
            )
        })

@app.route('/exercise-plan', methods=['POST'])
def generate_exercise_plan():
    data = request.get_json()

    # Extract relevant inputs, e.g. age, fitness level, goals, constraints
    age = data.get("age", "an adult")
    fitness_level = data.get("fitness_level", "beginner")
    goals = data.get("goals", "general fitness")
    constraints = data.get("constraints", "no constraints")

    # Build a prompt for the exercise plan request
    prompt = (
        f"Create a personalized exercise plan for a {age} year old individual "
        f"with a fitness level described as '{fitness_level}'. The main goals are: {goals}. "
        f"Consider the following constraints or limitations: {constraints}. "
        "Please provide a detailed weekly exercise plan including types of exercises, "
        "frequency, duration, and any important notes or tips."
    )

    response_text = call_openrouter_gpt(prompt)

    return jsonify({"exercise_plan": response_text})

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/journal')
def journal():
    return render_template('journal.html')

@app.route('/quiz/analyze-quiz', methods=['POST'])
def analyze_quiz():
    data = request.json
    quiz_type = data.get("quizType", "Unknown Quiz")
    score = data.get("score", 0)
    qa_pairs = data.get("qaPairs", "")

    severity = get_severity(quiz_type, score)
    summary = generate_quiz_summary(quiz_type, score, qa_pairs)
    return jsonify({"summary": summary, "severity": severity})

@app.route('/quiz/overall-summary', methods=['POST'])
def overall_summary():
    data = request.json
    quiz_summaries = data.get('quizSummaries', '')
    user_reflection = data.get('userReflection', '')

    prompt = f"""
        You are a compassionate mental health assistant.

        Here are the summaries of quizzes completed by the user:
        {quiz_summaries}

        The user also shared this reflection:
        {user_reflection}

        Please provide a thoughtful and empathetic overall summary that combines these insights. Keep it supportive and encourage next steps, but do not diagnose. 
        Also, make sure that this is lengthy and detailed (this was indeed a quiz), providing links and websites that others can use for support as well. 
    """

    summary = call_openrouter_gpt(prompt, max_tokens=300)
    return jsonify({"overallSummary": summary})

def generate_quiz_summary(quiz_type, score, qa_pairs):
    prompt = f"""
        You are a compassionate mental health assistant.
        A user has completed the {quiz_type.upper()} quiz with a total score of {score}.
        Here are the user's question-answer pairs:
        {qa_pairs}
        Please provide a clear, empathetic summary explaining what this score and answers might indicate. Avoid diagnosis. Suggest next steps.
        If severity is mild, note it's not cause for alarm but worth watching.
        Respond in 3-5 sentences.
    """
    return call_openrouter_gpt(prompt, max_tokens=250)

def get_severity(quiz_type, score):
    if quiz_type == 'phq9':
        return 'none' if score < 5 else 'mild' if score < 10 else 'moderate' if score < 15 else 'severe'
    if quiz_type == 'gad7':
        return 'none' if score < 5 else 'mild' if score < 10 else 'moderate' if score < 15 else 'severe'
    if quiz_type == 'ptsd':
        return 'none' if score < 8 else 'mild' if score < 14 else 'moderate' if score < 21 else 'severe'
    return 'unknown'


@app.route('/stats')
def stats_index():
    return render_template('statistics.html')

@app.route('/info')
def info():
    return render_template('info.html')

''' 
This is a sample of how the statistic page scripts could look (it still doesn't work yet -- Work in progress)

# Load and preprocess data on startup
data = pd.DataFrame()
forecast = pd.DataFrame()
model = None
sentiment_pipeline = None

try:
    data = pd.read_csv('user_data.csv')
    if data.empty:
        logger.warning("CSV file loaded but is empty.")
    else:
        data['date'] = pd.to_datetime(data['date'])

        imputer = KNNImputer(n_neighbors=5)
        data[['mood_score', 'anxiety_score']] = imputer.fit_transform(data[['mood_score', 'anxiety_score']])

        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
            revision="714eb0f"
        )
        data['journal_sentiment'] = data['journal_entries'].fillna('').apply(
            lambda x: sentiment_pipeline(x)[0]['label'] if x else 'NEUTRAL'
        )

        # Forecasting
        df_prophet = data[['date', 'mood_score']].rename(columns={"date": "ds", "mood_score": "y"})
        model = Prophet()
        model.fit(df_prophet)
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)

        # Clustering
        features = data[['mood_score', 'anxiety_score', 'sleep_quality']]
        features_scaled = StandardScaler().fit_transform(features)
        kmeans = KMeans(n_clusters=3)
        data['cluster'] = kmeans.fit_predict(features_scaled)

        pca = PCA(n_components=2)
        pca_components = pca.fit_transform(features_scaled)
        data['pca1'], data['pca2'] = pca_components[:, 0], pca_components[:, 1]

except Exception:
    logger.exception("Error during data loading or preprocessing")

def plot_to_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

def filter_date_range(dataframe, last_n_days=None):
    if last_n_days is None:
        return dataframe
    cutoff = datetime.now() - timedelta(days=last_n_days)
    return dataframe[dataframe['date'] >= cutoff]

@app.route('/stats/user_mood_trend')
def user_mood_trend():
    days = request.args.get('days', type=int)
    filtered = filter_date_range(df, days)
    daily_mood = filtered.groupby('date')['mood'].mean().reset_index()

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=daily_mood, x='date', y='mood', ax=ax)
    ax.set_title("Mood Over Time")
    ax.set_ylabel("Average Mood")
    ax.set_xlabel("Date")
    ax.grid(True)
    image_base64 = fig_to_base64(fig)

    prompt = (
        f"You are a mental health data expert. Explain the insights from a chart "
        f"showing average mood over time for the past {days if days else 'all'} days. "
        "Describe key trends, fluctuations, or anything notable."
    )
    explanation = call_openrouter_gpt(prompt)
    return jsonify(image=image_base64, explanation=explanation)


@app.route('/stats/mood_forecast')
def mood_forecast():
    days = request.args.get('days', default=30, type=int)
    filtered = filter_date_range(df, days)

    daily = filtered.groupby('date')['mood'].mean().reset_index()
    daily = daily.sort_values('date')
    daily['day_num'] = (daily['date'] - daily['date'].min()).dt.days

    model = LinearRegression()
    X = daily[['day_num']]
    y = daily['mood']
    model.fit(X, y)

    future_days = pd.DataFrame({'day_num': range(daily['day_num'].max()+1, daily['day_num'].max()+16)})
    forecast = model.predict(future_days)

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=daily, x='date', y='mood', label='Historical', ax=ax)
    future_dates = [daily['date'].max() + timedelta(days=i) for i in range(1,16)]
    ax.plot(future_dates, forecast, label='Forecast', linestyle='--')
    ax.set_title("Forecasted Mood (Next 15 Days)")
    ax.set_ylabel("Mood")
    ax.set_xlabel("Date")
    ax.legend()
    ax.grid(True)
    image_base64 = fig_to_base64(fig)

    prompt = (
        f"You are a mental health AI analyst. Explain a chart showing forecasted mood "
        f"over the next 15 days based on past data from the last {days} days. "
        "Describe what the forecast indicates about user mood trends."
    )
    explanation = call_openrouter_gpt(prompt)
    return jsonify(image=image_base64, explanation=explanation)


@app.route('/stats/cluster_plot')
def cluster_plot():
    days = request.args.get('days', default=30, type=int)
    filtered = filter_date_range(df, days)

    filtered['symptom_count'] = filtered['symptoms'].fillna('').apply(lambda x: len(x.split(',')) if x else 0)
    X = filtered[['mood', 'symptom_count']].dropna()
    if len(X) < 3:
        return jsonify(image="", explanation="Not enough data to perform cluster analysis."), 400

    kmeans = KMeans(n_clusters=3)
    filtered = filtered.loc[X.index]
    filtered['cluster'] = kmeans.fit_predict(X)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=filtered, x='mood', y='symptom_count', hue='cluster', palette='Set2', ax=ax)
    ax.set_title('Cluster Analysis: Mood vs Symptom Count')
    ax.set_xlabel('Mood')
    ax.set_ylabel('Number of Symptoms')
    ax.grid(True)
    image_base64 = fig_to_base64(fig)

    prompt = (
        f"Analyze a cluster plot that groups users based on mood and number of symptoms "
        f"over the last {days} days. Explain what these clusters might indicate about different user groups."
    )
    explanation = call_openrouter_gpt(prompt)
    return jsonify(image=image_base64, explanation=explanation)


@app.route('/stats/national_trend')
def national_trend():
    days = request.args.get('days', type=int)
    filtered = filter_date_range(df, days)
    daily_avg = filtered.groupby('date')['mood'].mean().reset_index()

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=daily_avg, x='date', y='mood', ax=ax, color='green')
    ax.set_title('National Mood Trend')
    ax.set_ylabel('Average Mood')
    ax.set_xlabel('Date')
    ax.grid(True)
    image_base64 = fig_to_base64(fig)

    prompt = (
        f"Explain a national mood trend chart showing average mood scores over the past "
        f"{days if days else 'all'} days across the country. "
        "Describe any patterns or changes in overall sentiment."
    )
    explanation = call_openrouter_gpt(prompt)
    return jsonify(image=image_base64, explanation=explanation)


@app.route('/stats/haiti_map')
def haiti_map():
    days = request.args.get('days', type=int)
    filtered = filter_date_range(df, days)
    region_mood = filtered.groupby('region')['mood'].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=region_mood.index, y=region_mood.values, palette='viridis', ax=ax)
    ax.set_title('Average Mood by Region')
    ax.set_ylabel('Average Mood')
    ax.set_xlabel('Region')
    ax.tick_params(axis='x', rotation=45)
    image_base64 = fig_to_base64(fig)

    prompt = (
        f"Explain the geographic distribution of average mood across regions in Haiti "
        f"over the last {days if days else 'all'} days. Highlight regions with notably high or low moods."
    )
    explanation = call_openrouter_gpt(prompt)
    return jsonify(image=image_base64, explanation=explanation)


@app.route('/stats/top_symptoms')
def top_symptoms():
    days = request.args.get('days', type=int)
    filtered = filter_date_range(df, days)
    symptoms_series = filtered['symptoms'].dropna().str.split(',').explode().str.strip()
    top_symptoms = symptoms_series.value_counts().head(10)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=top_symptoms.values, y=top_symptoms.index, palette='magma', ax=ax)
    ax.set_title('Top Reported Symptoms')
    ax.set_xlabel('Frequency')
    ax.set_ylabel('Symptom')
    image_base64 = fig_to_base64(fig)

    prompt = (
        f"Describe the most frequently reported mental health symptoms over the past "
        f"{days if days else 'all'} days and their potential impact."
    )
    explanation = call_openrouter_gpt(prompt)
    return jsonify(image=image_base64, explanation=explanation)


@app.route('/stats/intervention_efficacy')
def intervention_efficacy():
    days = request.args.get('days', type=int)
    filtered = filter_date_range(df, days)

    if 'intervention' not in filtered.columns:
        return jsonify(image="", explanation="No intervention data available."), 400

    intervention_avg = filtered.groupby('intervention')['mood'].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=intervention_avg.values, y=intervention_avg.index, palette='coolwarm', ax=ax)
    ax.set_title('Intervention Efficacy by Average Mood')
    ax.set_xlabel('Average Mood Score')
    ax.set_ylabel('Intervention')
    image_base64 = fig_to_base64(fig)

    prompt = (
        f"Analyze the efficacy of different mental health interventions based on average mood scores "
        f"reported in the last {days if days else 'all'} days."
    )
    explanation = call_openrouter_gpt(prompt)
    return jsonify(image=image_base64, explanation=explanation)


@app.route('/stats/age_demographics')
def age_demographics():
    days = request.args.get('days', type=int)
    filtered = filter_date_range(df, days)
    age_groups = pd.cut(filtered['age'], bins=[0,18,30,45,60,100], labels=['0-17','18-29','30-44','45-59','60+'])
    age_dist = age_groups.value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=age_dist.index, y=age_dist.values, palette='Spectral', ax=ax)
    ax.set_title('Demographics by Age Group')
    ax.set_xlabel('Age Group')
    ax.set_ylabel('Number of Users')
    image_base64 = fig_to_base64(fig)

    prompt = (
        f"Explain the distribution of users across different age groups in the last "
        f"{days if days else 'all'} days and any notable demographic trends."
    )
    explanation = call_openrouter_gpt(prompt)
    return jsonify(image=image_base64, explanation=explanation)


@app.route('/stats/ai_summary')
def ai_summary():
    mood_avg = df['mood'].mean()
    symptom_counts = df['symptoms'].dropna().str.split(',').explode().value_counts().head(3)
    top_symptoms = ', '.join(symptom_counts.index.tolist())
    summary = (
        f"Average user mood is {mood_avg:.2f}. "
        f"Most commonly reported symptoms include {top_symptoms}. "
        "Monitoring these trends can help inform targeted mental health interventions."
    )
    return jsonify(summary=summary)
    
'''

DB_FILE = "journal_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except:
        return False

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
    data = request.json
    required_fields = ["content", "mood", "tags", "habits", "goals"]
    for field in required_fields:
        if field not in data:
            return abort(400, description=f"Missing field: {field}")

    db = load_db()
    # Store entire entry
    db[date] = {
        "content": data["content"],
        "mood": data["mood"],
        "tags": data["tags"],
        "habits": data["habits"],
        "goals": data["goals"]
    }
    save_db(db)
    return jsonify({"status": "saved", "date": date})

@app.route("/api/journal/search", methods=["GET"])
def search_entries():
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify([])

    db = load_db()
    results = []
    for date, entry in db.items():
        combined_text = (entry.get("content", "") + " " + " ".join(entry.get("tags", []))).lower()
        if query in combined_text:
            results.append({
                "date": date,
                "content": entry.get("content", ""),
                "mood": entry.get("mood", None),
                "tags": entry.get("tags", [])
            })

    # Sort newest first
    results.sort(key=lambda e: e["date"], reverse=True)
    return jsonify(results)

@app.route("/api/journal/all", methods=["GET"])
def get_all_entries():
    db = load_db()
    entries = []
    for date, entry in db.items():
        entries.append({
            "date": date,
            "content": entry.get("content", ""),
            "mood": entry.get("mood", None),
            "tags": entry.get("tags", [])
        })
    # Sort newest first
    entries.sort(key=lambda e: e["date"], reverse=True)
    return jsonify(entries)

@app.route("/api/ai/sentiment", methods=["POST"])
def sentiment_analysis():
    data = request.json
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


@app.route("/api/ai/summary", methods=["POST"])
def summary_generation():
    data = request.json
    text = data.get("text", "")
    if not text:
        return abort(400, description="Missing text for summary generation")

    prompt = f"""
    You are a compassionate mental wellness assistant. First, summarize the following journal entry in 2–3 emotionally-aware sentences. Then, suggest 2–3 practical, mindfulness-based techniques the user could try based on the content — such as breathing, journaling, gratitude exercises, or setting boundaries.

    {text}
    """
    result = call_openrouter_gpt(prompt)
    return jsonify({"summary": result})


@app.route("/api/ai/moodtrend", methods=["GET"])
def mood_trend_summary():
    db = load_db()
    today = datetime.today()
    past_week_dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    entries = [db[date] for date in past_week_dates if date in db]
    if not entries:
        return abort(404, description="No journal entries in the past 7 days")

    combined_text = "\n\n".join(
        f"Date: {date}\nMood: {entry['mood']}\nEntry: {entry['content']}"
        for date, entry in zip(past_week_dates, entries)
    )

    prompt = f"""
    Review the following journal entries from the past week. Provide a 2–3 paragraph summary of the emotional and mood trends, any recurring themes, and suggestions for next steps. Be thoughtful, positive, and insightful:

    {combined_text}
    """
    result = call_openrouter_gpt(prompt, max_tokens=1000)
    return jsonify({"mood_trend": result})


# --- ANALYTICS ---

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

    # Mood options for validation
    valid_moods = {"happy","calm","neutral","sad","anxious","angry"}

    for i in range(days):
        d = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        entry = db.get(date_str)
        mood = entry.get("mood") if entry and entry.get("mood") in valid_moods else None
        trend.append({"date": date_str, "mood": mood})

    trend.reverse()  # Oldest to newest
    return jsonify(trend)

@app.route("/connections")
def connections_page():
    people = [
        {
            "name": "Dr. Lena Kapoor",
            "role": "Licensed Therapist (CBT, Anxiety)",
            "bio": "Over 12 years of experience helping clients manage anxiety and emotional stress.",
            "avatar": "https://randomuser.me/api/portraits/women/44.jpg",
            "social": {
                "linkedin": "https://linkedin.com/in/lenakapoor",
                "twitter": "",
                "instagram": ""
            }
        },
        {
            "name": "Carlos Mendes",
            "role": "Peer Support - PTSD & Mindfulness",
            "bio": "Army veteran and peer mentor focused on trauma recovery and grounding techniques.",
            "avatar": "https://randomuser.me/api/portraits/men/32.jpg",
            "social": {
                "linkedin": "",
                "twitter": "https://twitter.com/mentalcarlos",
                "instagram": "https://instagram.com/ptsd_recovery"
            }
        },
        {
            "name": "Fatima Zahra",
            "role": "Wellness Coach & Yoga Teacher",
            "bio": "Combining movement and mindset to support emotional balance and resilience.",
            "avatar": "https://randomuser.me/api/portraits/women/68.jpg",
            "social": {
                "linkedin": "https://linkedin.com/in/fatima-wellness",
                "twitter": "",
                "instagram": "https://instagram.com/yogawithfatima"
            }
        },
        {
            "name": "Dante Rivers",
            "role": "Peer Support - Anxiety & Depression",
            "bio": "I've been there. Let's walk through the fog together.",
            "avatar": "https://randomuser.me/api/portraits/men/75.jpg",
            "social": {
                "linkedin": "",
                "twitter": "",
                "instagram": "https://instagram.com/mental.dante"
            }
        },
        {
            "name": "Sophia Lee, PsyD",
            "role": "Clinical Psychologist",
            "bio": "Empowering individuals with practical tools for emotional clarity and healing.",
            "avatar": "https://randomuser.me/api/portraits/women/27.jpg",
            "social": {
                "linkedin": "https://linkedin.com/in/drsophialee",
                "twitter": "",
                "instagram": ""
            }
        },
        {
            "name": "Jayden Ross",
            "role": "Peer Support - Grief & Loss",
            "bio": "Helping others find meaning and strength after personal loss.",
            "avatar": "https://randomuser.me/api/portraits/men/41.jpg",
            "social": {
                "linkedin": "",
                "twitter": "https://twitter.com/jaydenlistens",
                "instagram": ""
            }
        }
    ]

    return render_template("connections.html", people=people)

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        print(f"Creating database {DB_FILE}...")
        init_db()
    app.run(debug=True)
