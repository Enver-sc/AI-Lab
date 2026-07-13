import re

PATTERNS = {
    "E-Mail-Adresse": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    "API-Schlüssel": r"\b(?:sk|pk|api)[-_][A-Za-z0-9_-]{12,}\b",
    "Bearer-Token": r"\bBearer\s+[A-Za-z0-9._~+/=-]{10,}",
    "Privater Schlüssel": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    # Erkennt sowohl technische Schreibweisen (password=secret) als auch
    # natürliche Sätze wie "mein Passwort ist secret".
    "Passwort": r"(?i)\b(?:passwort|password|pwd)\s*(?::|=|ist\b|lautet\b|heißt\b|heisst\b)\s*[\"']?\S+",
}
KEYWORDS = {
    "Gesundheitsdaten": (r"(?i)\b(diagnose|patient|krankheit|medikament|gesundheitsdaten)\b", 18),
    "Finanzdaten": (r"(?i)\b(kontostand|steuererklärung|gehalt|finanzdaten)\b", 14),
    "Vertrauliche Informationen": (r"(?i)\b(vertraulich|geschäftsgeheimnis|internal only|nda)\b", 18),
    "Schädliche oder rechtswidrige Anfrage": (r"(?i)\b(hacken|ransomware|bombe bauen|betrug begehen|diskriminier)\b", 35),
    "Urheberrechtsrisiko": (r"(?i)\b(vollständig(?:e[nrms]?)? (?:buch|artikel|songtext)|urheberrechtlich)\b", 12),
    "Geheimnis im Klartext": (r"(?i)\b(?:im\s+)?klartext\b", 20),
}

def _luhn_valid(digits):
    total = 0
    for position, char in enumerate(reversed(digits)):
        value = int(char)
        if position % 2 == 1:
            value *= 2
            if value > 9: value -= 9
        total += value
    return total % 10 == 0

def _valid_credit_card(candidate):
    digits = re.sub(r"\D", "", candidate)
    return 13 <= len(digits) <= 19 and _luhn_valid(digits)

def _valid_iban(candidate):
    iban = re.sub(r"\s", "", candidate).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", iban): return False
    # Deutsche IBANs sind immer 22-stellig und rein numerisch nach dem Ländercode.
    if iban.startswith("DE") and (len(iban) != 22 or not iban[2:].isdigit()): return False
    rearranged = iban[4:] + iban[:4]
    return int("".join(str(int(char, 36)) for char in rearranged)) % 97 == 1

def _valid_steuer_id(candidate):
    digits = re.sub(r"\D", "", candidate)
    if len(digits) != 11 or digits[0] == "0": return False
    # Strukturregel: genau eine Ziffer kommt in den ersten zehn Stellen doppelt
    # oder dreifach vor, bei Dreifachvorkommen nie direkt hintereinander.
    first_ten = digits[:10]
    repeated = [d for d in set(first_ten) if first_ten.count(d) > 1]
    if len(repeated) != 1 or first_ten.count(repeated[0]) not in (2, 3): return False
    if first_ten.count(repeated[0]) == 3 and repeated[0] * 3 in first_ten: return False
    # Prüfziffer nach ISO 7064 (MOD 11,10), wie vom BZSt vorgegeben.
    product = 10
    for char in first_ten:
        total = (int(char) + product) % 10 or 10
        product = (total * 2) % 11
    return (11 - product) % 10 == int(digits[10])

def _valid_phone(candidate):
    digits = re.sub(r"\D", "", candidate)
    national = digits[2:] if candidate.lstrip().startswith("+49") else digits[1:]
    return 7 <= len(national) <= 11 and not national.startswith("0")

# Kandidaten findet die Regex, bestätigt wird per Prüfsumme bzw. Strukturregel.
# Die Lookarounds verhindern Treffer innerhalb längerer Ziffernfolgen sowie in
# Dezimalzahlen (Preise wie 1.250,50); normale Satzzeichen nach der Zahl bleiben
# erlaubt. IBANs werden kompakt oder in 4er-Gruppen erkannt.
VALIDATED_PATTERNS = {
    "Telefonnummer": (r"(?<![\d+])(?<!\d[.,])(?:\+49[ \-/]?|0)[1-9](?:[ \-/]?\d){5,12}(?!\d)(?![.,]\d)", _valid_phone),
    "IBAN": (r"\b[A-Z]{2}\d{2}(?:[A-Z0-9]{11,30}|(?: [A-Z0-9]{4}){2,7}(?: [A-Z0-9]{1,4})?)\b", _valid_iban),
    "Kreditkartennummer": (r"(?<!\d)(?<!\d[.,])(?:\d[ \-]?){12,18}\d(?!\d)(?![.,]\d)", _valid_credit_card),
    "Deutsche Steuer-ID": (r"(?<!\d)(?<!\d[.,])\d{11}(?!\d)(?![.,]\d)", _valid_steuer_id),
}

# Deckelung: jede Kategorie zählt höchstens einmal; schwache Heuristik-Treffer
# zusammen höchstens WEAK_TOTAL_CAP Punkte, damit viele unsichere Signale allein
# nie eine rote Bewertung erzwingen. Die Ampel-Schwellen (80/50) bleiben gleich.
PATTERN_PENALTY = 18
WEAK_FINDINGS = {"Telefonnummer", "Urheberrechtsrisiko", "Geheimnis im Klartext"}
WEAK_TOTAL_CAP = 35

def inspect_prompt(text):
    findings, strong_penalty, weak_penalty = [], 0, 0
    def add(label, amount):
        nonlocal strong_penalty, weak_penalty
        findings.append(label)
        if label in WEAK_FINDINGS: weak_penalty += amount
        else: strong_penalty += amount
    for label, pattern in PATTERNS.items():
        if re.search(pattern, text, re.I): add(label, PATTERN_PENALTY)
    for label, (pattern, validator) in VALIDATED_PATTERNS.items():
        if any(validator(m.group(0)) for m in re.finditer(pattern, text, re.I)): add(label, PATTERN_PENALTY)
    for label, (pattern, amount) in KEYWORDS.items():
        if re.search(pattern, text): add(label, amount)
    penalty = strong_penalty + min(weak_penalty, WEAK_TOTAL_CAP)
    score = max(0, 100 - min(100, penalty))
    return {"score": score, "level": "green" if score >= 80 else "yellow" if score >= 50 else "red", "findings": findings, "contains_personal_data": any(x in findings for x in ("E-Mail-Adresse", "Telefonnummer", "IBAN", "Kreditkartennummer", "Deutsche Steuer-ID", "Gesundheitsdaten")), "contains_confidential_data": any(x in findings for x in ("API-Schlüssel", "Bearer-Token", "Privater Schlüssel", "Passwort", "Vertrauliche Informationen", "Geheimnis im Klartext"))}

def redact_sensitive(text):
    def masked(match):
        value = match.group(0)
        return (value[:3] + "***" + value[-4:]) if len(value) > 8 else "***"
    for pattern in PATTERNS.values(): text = re.sub(pattern, masked, text, flags=re.I)
    for pattern, validator in VALIDATED_PATTERNS.values():
        text = re.sub(pattern, lambda m: masked(m) if validator(m.group(0)) else m.group(0), text, flags=re.I)
    return text
