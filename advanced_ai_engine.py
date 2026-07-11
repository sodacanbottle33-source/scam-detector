import re

MODEL_NAME = "ProtectAI/deberta-v3-base-prompt-injection-v2"

_ai_model = None


def _load_ai_model():
    global _ai_model

    if _ai_model is None:
        from transformers import pipeline

        print("Loading advanced scam detector on demand...")

        _ai_model = pipeline(
            "text-classification",
            model=MODEL_NAME,
            truncation=True,
            device=-1,
        )

    return _ai_model


def rule_score(text):
    text_lower = text.lower()
    score = 0
    reasons = []

    scam_patterns = {
        "Urgency": [
            "urgent",
            "act now",
            "immediately",
            "last chance",
            "final warning",
            "within 24 hours",
            "account will be closed",
        ],
        "Banking": [
            "bank account",
            "account locked",
            "verify your account",
            "unauthorized transaction",
            "security alert",
            "payment failed",
        ],
        "Money": [
            "send money",
            "wire transfer",
            "gift card",
            "bitcoin",
            "crypto",
            "refund fee",
            "processing fee",
            "cash app",
            "paypal",
        ],
        "Phishing": [
            "click here",
            "verify here",
            "login now",
            "reset password",
            "confirm your identity",
            "update payment",
        ],
        "Impersonation": [
            "irs",
            "government",
            "police",
            "microsoft support",
            "amazon support",
            "paypal support",
            "bank security",
        ],
        "Prize": [
            "you won",
            "claim your prize",
            "winner",
            "lottery",
            "free iphone",
            "cash reward",
            "congratulations",
        ],
        "Family Scam": [
            "lost my phone",
            "new number",
            "don't tell anyone",
            "i need money",
            "emergency",
            "can you send",
        ],
    }

    for category, phrases in scam_patterns.items():
        for phrase in phrases:
            if phrase in text_lower:
                score += 12
                reasons.append(f"{category}: {phrase}")

    if re.search(r"https?://|www\.", text):
        score += 18
        reasons.append("Suspicious link detected")

    if re.search(r"\+?\d[\d\s\-()]{7,}", text):
        score += 8
        reasons.append("Phone number detected")

    if re.search(r"\$|usd|yen|dollar|payment|fee", text_lower):
        score += 10
        reasons.append("Money/payment language detected")

    if text.count("!") >= 3:
        score += 6
        reasons.append("High-pressure punctuation detected")

    return min(score, 100), reasons


def analyze_message(text):
    rules, rule_reasons = rule_score(text)

    try:
        ai_model = _load_ai_model()
        ai_result = ai_model(text)[0]

        ai_confidence = int(float(ai_result["score"]) * 100)
        ai_label = str(ai_result["label"])

        final_score = int(
            (rules * 0.75)
            + (ai_confidence * 0.25)
        )

        if final_score >= 70:
            level = "SCAM"
        elif final_score >= 40:
            level = "SUSPICIOUS"
        else:
            level = "SAFE"

        reasons = list(rule_reasons)
        reasons.append(f"AI model label: {ai_label}")
        reasons.append(f"AI confidence: {ai_confidence}%")
        reasons.append(f"Rule score: {rules}/100")

        if not rule_reasons and final_score < 40:
            reasons.append("No strong scam signals found.")

        return {
            "score": final_score,
            "level": level,
            "reasons": reasons,
        }

    except Exception as error:
        if rules >= 70:
            level = "SCAM"
        elif rules >= 40:
            level = "SUSPICIOUS"
        else:
            level = "SAFE"

        fallback_reasons = list(rule_reasons)
        fallback_reasons.append(
            f"AI model unavailable, used rule engine: {error}"
        )

        if not rule_reasons:
            fallback_reasons.append(
                "No strong scam signals found."
            )

        return {
            "score": rules,
            "level": level,
            "reasons": fallback_reasons,
        }


if __name__ == "__main__":
    print("Advanced scam detector ready.")