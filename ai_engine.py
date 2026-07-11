import re

def analyze_message(text):
    original_text = text
    text = text.lower()

    score = 0
    reasons = []

    categories = {
        "Urgency":[
            "urgent","immediately","act now","respond now","last chance",
            "limited time","expires","deadline","within 24 hours",
            "final warning","important notice","action required"
        ],
        "Banking":[
            "bank","bank account","verify account","account suspended",
            "routing number","credit card","debit card","security alert",
            "wire transfer","payment failed"
        ],
        "Passwords":[
            "password","login","sign in","verification code",
            "otp","2fa","security code","reset password"
        ],
        "Crypto":[
            "bitcoin","ethereum","crypto","wallet","coinbase",
            "binance","seed phrase","private key","usdt"
        ],
        "GiftCards":[
            "gift card","apple gift card","steam card",
            "amazon gift card","google play card"
        ],
        "Money":[
            "paypal","cash app","venmo","western union",
            "moneygram","invoice","refund","transaction"
        ],
        "Government":[
            "irs","tax office","government","police",
            "court","social security"
        ],
        "Giveaways":[
            "you won","winner","claim prize","free money",
            "lottery","jackpot","reward"
        ]
    }

    for category, words in categories.items():
        for word in words:
            if word in text:
                score += 8
                reasons.append(f"{category}: {word}")

    if re.search(r'https?://|www\.', original_text):
        score += 20
        reasons.append("Suspicious link detected")

    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", original_text):
        score += 10
        reasons.append("Email address detected")

    if re.search(r"\+?\d[\d\s\-()]{7,}", original_text):
        score += 10
        reasons.append("Phone number detected")

    if "$" in original_text or "usd" in text:
        score += 5
        reasons.append("Money request detected")

    if original_text.count("!") >= 3:
        score += 5
        reasons.append("Aggressive punctuation")

    score = min(score,100)

    if score >= 70:
        level="SCAM"
    elif score >= 40:
        level="SUSPICIOUS"
    else:
        level="SAFE"

    if not reasons:
        reasons.append("No obvious scam indicators found.")

    return {
        "score": score,
        "level": level,
        "reasons": reasons
    }
