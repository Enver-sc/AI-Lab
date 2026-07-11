from cryptography.fernet import Fernet, InvalidToken

class EncryptionUnavailable(ValueError): pass

class EncryptionService:
    def __init__(self, key):
        self.key = key
    def _fernet(self):
        if not self.key: raise EncryptionUnavailable("APP_ENCRYPTION_KEY fehlt; API-Schlüssel können nicht gespeichert werden.")
        try: return Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
        except (ValueError, TypeError) as exc: raise EncryptionUnavailable("APP_ENCRYPTION_KEY ist kein gültiger Fernet-Schlüssel.") from exc
    def encrypt(self, value): return self._fernet().encrypt(value.encode()).decode() if value else None
    def decrypt(self, value):
        if not value: return ""
        try: return self._fernet().decrypt(value.encode()).decode()
        except InvalidToken as exc: raise EncryptionUnavailable("API-Schlüssel kann nicht entschlüsselt werden.") from exc

def mask_secret(value):
    if not value: return ""
    if len(value) <= 8: return "***"
    prefix = value[:3] if value.startswith(("sk-", "pk-")) else value[:2]
    return f"{prefix}***{value[-4:]}"

