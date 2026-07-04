import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# ---------------- SAMPLE TRAINING DATA ----------------
texts = [
    "your account is suspended click here",
    "you won a free prize claim now",
    "urgent action required verify bank",
    "hello how are you today",
    "let's meet tomorrow",
    "your password has been reset",
    "bitcoin investment opportunity",
    "family dinner tonight"
]

labels = [
    1, 1, 1, 0, 0, 1, 1, 0   # 1 = scam, 0 = safe
]

# ---------------- VECTORIZE TEXT ----------------
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

# ---------------- TRAIN MODEL ----------------
model = LogisticRegression()
model.fit(X, labels)

# ---------------- SAVE MODEL ----------------
joblib.dump(model, "model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("Model trained and saved!")