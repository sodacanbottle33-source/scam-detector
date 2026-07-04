import re

SCAM_KEYWORDS = [
    "urgent", "immediately", "act now", "bank", "verify",
    "password", "login", "suspended", "gift card",
    "bitcoin", "wiring money", "click link"
]

def analyze_message(text):

    text = text.lower()

    score = 0
    reasons = []

    # 1. keyword detection
    for word in SCAM_KEYWORDS:
        if word in text:
            score += 15
            reasons.append(f"Found scam trigger word: '{word}'")

    # 2. urgency detection
    if re.search(r"now|immediately|urgent|today", text):
        score += 20
        reasons.append("High urgency language detected")

    # 3. impersonation patterns
    if "bank" in text or "irs" in text:
        score += 20
        reasons.append("Possible authority impersonation")

    # 4. link bait
    if "http" in text or "www" in text:
        score += 25
        reasons.append("Suspicious link detected")

    # cap score
    if score > 100:
        score = 100

    # level
    if score < 30:
        level = "SAFE"
    elif score < 60:
        level = "SUSPICIOUS"
    else:
        level = "SCAM"

    return {
        "score": score,
        "level": level,
        "reasons": reasons
    }
🚀 STEP 2 — Update dashboard display (IMPORTANT)

In your dashboard.html, where you show results, add:

{% if result %}
<div style="margin-top:20px; text-align:left;">

    <h3>🧠 AI Analysis</h3>

    <p><b>Score:</b> {{ result.score }}/100</p>
    <p><b>Level:</b> {{ result.level }}</p>

    <ul>
        {% for r in result.reasons %}
            <li>{{ r }}</li>
        {% endfor %}
    </ul>

</div>
{% endif %}