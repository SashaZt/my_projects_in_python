import base64
import os

from config import SECRET_AES_KEY
from configuration.logger_setup import logger
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def encrypt_access_key(access_key: str) -> str:
    logger.info("Шифрование ключа доступа")
    iv = os.urandom(16)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(access_key.encode()) + padder.finalize()

    cipher = Cipher(
        algorithms.AES(SECRET_AES_KEY), modes.CBC(iv), backend=default_backend()
    )
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    encrypted_key = base64.b64encode(iv + encrypted_data).decode()
    logger.info("Ключ доступа успешно зашифрован")
    return encrypted_key
