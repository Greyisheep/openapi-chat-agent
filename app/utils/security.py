from cryptography.fernet import Fernet
import base64
import os


_key_env = "PLATFORM_ENC_KEY"


def _get_fernet() -> Fernet:
	key = os.getenv(_key_env)
	if not key:
		key = base64.urlsafe_b64encode(os.urandom(32)).decode()
		os.environ[_key_env] = key
	return Fernet(key)


def encrypt_api_key(raw: str) -> str:
	f = _get_fernet()
	return f.encrypt(raw.encode()).decode()


def decrypt_api_key(token: str) -> str:
	f = _get_fernet()
	return f.decrypt(token.encode()).decode()









