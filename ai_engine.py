import joblib

# load model
model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

def analyze_message(text):

    X = vectorizer.transform([text])

    prediction = model.predict(X)[0]
    prob = model.predict_proba(X)[0][1]  # scam probability

    score = int(prob * 100)

    if prediction == 1:
        level = "SCAM"
    elif score > 40:
        level = "SUSPICIOUS"
    else:
        level = "SAFE"

    reasons = []

    if prediction == 1:
        reasons.append("ML model detected scam patterns")
    else:
        reasons.append("ML model considers message low risk")

    return {
        "score": score,
        "level": level,
        "reasons": reasons
    }