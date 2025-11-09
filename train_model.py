import pickle
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

# ===================================================
# 🎯 TRAINING DATA (Expanded for mental stress domain)
# ===================================================
data = {
    "text": [
        # High stress / anxiety
        "I feel anxious and can’t stop overthinking",
        "My workload is overwhelming",
        "I can’t sleep, everything feels heavy",
        "I’m exhausted and losing focus",
        "I’m mentally drained and want to cry",
        "Exams make me panic every night",
        "Too much pressure, I can’t handle it anymore",
        "Everything feels out of control and chaotic",

        # Medium stress
        "I’m stressed but I can handle it",
        "I feel a bit tense but trying to relax",
        "Work is hectic but manageable",
        "I’m tired from studying all week",
        "I feel pressure but not too much",
        "I’m low on energy today",
        "I feel down, but I’ll bounce back soon",

        # Low stress / calm
        "I’m calm and peaceful today",
        "Everything feels balanced and okay",
        "I’m grateful for the quiet moments",
        "I feel light and relaxed",
        "I’m content with how things are",
        "I’m focused and motivated today",
        "I feel mentally clear",

        # Work/Academic stress
        "Deadlines are stressing me out",
        "Too many assignments due this week",
        "My exams are making me panic",
        "Workload keeps increasing every day",
        "I’m burned out from continuous studying",
        "College projects are draining my mind",

        # Relationship stress
        "My partner and I had a fight",
        "I feel lonely and ignored",
        "Breakups are emotionally exhausting",
        "I miss my friend, it’s depressing",
        "No one understands me lately",
        "My relationship is falling apart",

        # Positive / happy / calmful
        "I feel happy and positive today",
        "Everything is going well in life",
        "I’m relaxed and mentally stable",
        "Feeling peaceful and grateful",
        "I’m excited about the future",
        "I feel good and confident about myself"
    ],
    "label": [
        "High Stress", "High Stress", "High Stress", "High Stress", "High Stress", "High Stress", "High Stress", "High Stress",
        "Medium Stress", "Medium Stress", "Medium Stress", "Medium Stress", "Medium Stress", "Medium Stress", "Medium Stress",
        "Low Stress", "Low Stress", "Low Stress", "Low Stress", "Low Stress", "Low Stress", "Low Stress",
        "Work/Academic", "Work/Academic", "Work/Academic", "Work/Academic", "Work/Academic", "Work/Academic",
        "Relationship", "Relationship", "Relationship", "Relationship", "Relationship", "Relationship",
        "Calm/Positive", "Calm/Positive", "Calm/Positive", "Calm/Positive", "Calm/Positive", "Calm/Positive"
    ]
}

df = pd.DataFrame(data)
print(f"🧩 Loaded {len(df)} training samples.")

# ===================================================
# ⚙️ TRAIN MODEL
# ===================================================
X_train, X_test, y_train, y_test = train_test_split(df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"])

vectorizer = TfidfVectorizer(max_features=4000, stop_words="english", ngram_range=(1,2))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

model = LogisticRegression(max_iter=1500, C=2.0)
model.fit(X_train_vec, y_train)

y_pred = model.predict(X_test_vec)
print("\n✅ Accuracy:", round(accuracy_score(y_test, y_pred) * 100, 2), "%")
print("\n", classification_report(y_test, y_pred))

# ===================================================
# 💾 SAVE MODEL
# ===================================================
os.makedirs("model", exist_ok=True)
pickle.dump((vectorizer, model), open("model/emotion_model.pkl", "wb"))
print("\n✅ ML Model saved successfully at model/emotion_model.pkl")
