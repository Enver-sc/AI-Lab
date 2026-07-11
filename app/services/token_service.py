def estimate_tokens(text: str) -> int:
    return max(1, round(len(text or "") / 4))

