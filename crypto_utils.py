from cryptography.fernet import Fernet
from pathlib import Path

KEYFILE = Path(__file__).with_name("secret.key")

def generate_key():
    key = Fernet.generate_key()
    KEYFILE.write_bytes(key)
    return key

def load_key():
    if not KEYFILE.exists():
        return generate_key()
    return KEYFILE.read_bytes()

def encrypt_str(plaintext: str) -> str:
    if plaintext is None:
        plaintext = ""
    key = load_key()
    f = Fernet(key)
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")  # store as text

def decrypt_str(token_str: str) -> str:
    if token_str is None or token_str == "":
        return ""
    key = load_key()
    f = Fernet(key)
    try:
        plain = f.decrypt(token_str.encode("utf-8"))
        return plain.decode("utf-8")
    except Exception:
        # If decryption fails, return the token (or empty) to avoid crashing
        return ""