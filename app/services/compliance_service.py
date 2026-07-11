import re

PATTERNS = {
    "E-Mail-Adresse": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    "Telefonnummer": r"(?<!\w)(?:\+?\d[\d ()/-]{7,}\d)",
    "IBAN": r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}\b",
    "API-Schlüssel": r"\b(?:sk|pk|api)[-_][A-Za-z0-9_-]{12,}\b",
    "Bearer-Token": r"\bBearer\s+[A-Za-z0-9._~+/=-]{10,}",
    "Privater Schlüssel": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    # Erkennt sowohl technische Schreibweisen (password=secret) als auch
    # natürliche Sätze wie "mein Passwort ist secret".
    "Passwort": r"(?i)\b(?:passwort|password|pwd)\s*(?::|=|ist\b|lautet\b|heißt\b|heisst\b)\s*[\"']?\S+",
    "Kreditkartennummer": r"\b(?:\d[ -]*?){13,19}\b",
}
KEYWORDS = {
    "Gesundheitsdaten": (r"(?i)\b(diagnose|patient|krankheit|medikament|gesundheitsdaten)\b", 18),
    "Finanzdaten": (r"(?i)\b(kontostand|steuererklärung|gehalt|finanzdaten)\b", 14),
    "Vertrauliche Informationen": (r"(?i)\b(vertraulich|geschäftsgeheimnis|internal only|nda)\b", 18),
    "Schädliche oder rechtswidrige Anfrage": (r"(?i)\b(hacken|ransomware|bombe bauen|betrug begehen|diskriminier)\b", 35),
    "Urheberrechtsrisiko": (r"(?i)\b(vollständig(?:e[nrms]?)? (?:buch|artikel|songtext)|urheberrechtlich)\b", 12),
    "Geheimnis im Klartext": (r"(?i)\b(?:im\s+)?klartext\b", 20),
}

def inspect_prompt(text):
    findings, penalty = [], 0
    for label, pattern in PATTERNS.items():
        if re.search(pattern, text, re.I): findings.append(label); penalty += 18
    for label, (pattern, amount) in KEYWORDS.items():
        if re.search(pattern, text): findings.append(label); penalty += amount
    score = max(0, 100 - min(100, penalty))
    return {"score": score, "level": "green" if score >= 80 else "yellow" if score >= 50 else "red", "findings": findings, "contains_personal_data": any(x in findings for x in ("E-Mail-Adresse", "Telefonnummer", "IBAN", "Kreditkartennummer", "Gesundheitsdaten")), "contains_confidential_data": any(x in findings for x in ("API-Schlüssel", "Bearer-Token", "Privater Schlüssel", "Passwort", "Vertrauliche Informationen", "Geheimnis im Klartext"))}

def redact_sensitive(text):
    def masked(match):
        value = match.group(0)
        return (value[:3] + "***" + value[-4:]) if len(value) > 8 else "***"
    for pattern in PATTERNS.values(): text = re.sub(pattern, masked, text, flags=re.I)
    return text
