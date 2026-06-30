import re
import math

def analyze_message(message):

    text = message.lower()
    words = text.split()

    score = 0
    reasons = []

    # =========================
    # 🧠 SCAM ARCHETYPE SYSTEM
    # =========================

    archetypes = {
        "money_grab": ["money", "send", "pay", "transfer", "cash", "give me"],
        "identity_theft": ["password", "otp", "ssn", "login", "verify"],
        "fear_attack": ["suspended", "locked", "arrest", "legal", "police"],
        "urgency": ["now", "immediately", "urgent", "hurry", "fast"],
        "manipulation": ["trust me", "secret", "dont tell", "confidential"]
    }

    archetype_hits = {}

    for name, keywords in archetypes.items():
        hits = sum(1 for k in keywords if k in text)
        if hits > 0:
            archetype_hits[name] = hits
            score += hits * 15

    # =========================
    # 🧠 PATTERN STACKING (VERY POWERFUL)
    # =========================
    if len(archetype_hits) >= 2:
        score += 20
        reasons.append("🧠 Multi-vector scam pattern detected")

    if len(archetype_hits) >= 3:
        score += 25
        reasons.append("🚨 Coordinated scam structure detected")

    # =========================
    # 🔗 LINK ANALYSIS
    # =========================
    if "http" in text or "www" in text:
        score += 25
        reasons.append("🔗 Phishing link detected")

    # =========================
    # 🔊 HUMAN BEHAVIOR MODEL
    # =========================

    caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)

    if caps_ratio > 0.5 and len(message) > 20:
        score += 20
        reasons.append("📢 Aggressive communication pattern")

    if "!!" in message:
        score += 10
        reasons.append("❗ Emotional pressure detected")

    # =========================
    # 🧬 ENTROPY / RANDOMNESS ANALYSIS
    # =========================
    unique_words = len(set(words))
    word_count = len(words)

    if word_count > 0:
        entropy = unique_words / word_count

        if entropy < 0.4:
            score += 10
            reasons.append("🧬 Repetitive / scripted message detected")

    # =========================
    # 💰 EXTREME MONEY REQUEST DETECTION
    # =========================

    if "all your money" in text:
        score += 40
        reasons.append("🚨 Direct asset theft pattern")

    # =========================
    # 🧮 FINAL NORMALIZATION
    # =========================

    score = min(100, score)

    # =========================
    # 🎯 LEVEL ENGINE
    # =========================

    if score >= 85:
        level = "🚨 CRITICAL THREAT"
    elif score >= 65:
        level = "🔴 HIGH RISK"
    elif score >= 40:
        level = "🟠 MEDIUM RISK"
    elif score >= 15:
        level = "🟡 LOW RISK"
    else:
        level = "🟢 SAFE"

    # =========================
    # 📊 CONFIDENCE MODEL
    # =========================
    confidence = min(100, score + (len(archetype_hits) * 5))

    # =========================
    # 🧾 FINAL OUTPUT
    # =========================

    explanation = " | ".join(reasons) if reasons else "No suspicious patterns found"

    return {
        "score": score,
        "level": level,
        "confidence": confidence,
        "archetypes": list(archetype_hits.keys()),
        "explanation": explanation
    }