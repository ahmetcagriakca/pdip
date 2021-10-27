from cryptography.fernet import Fernet
from injector import inject

from ..configuration.models.application import ApplicationConfig
from ..dependency import IScoped


class CryptoService(IScoped):
    @inject
    def __init__(self, application_config: ApplicationConfig):
        self.application_config = application_config

    def decrypt(self, data):
        encoded_data = data.encode()
        secret_key = self.application_config.secret_key.encode()
        f = Fernet(secret_key)
        decrypted_data = f.decrypt(encoded_data)
        decoded_decrypted_data = decrypted_data.decode()
        return decoded_decrypted_data

    def encrypt(self, data: str):
        encoded_data = data.encode()
        secret_key = self.application_config.secret_key.encode()
        f = Fernet(secret_key)
        encrypted_data = f.encrypt(encoded_data)
        decoded_encrypted_data = encrypted_data.decode()
        return decoded_encrypted_data

    @classmethod
    def generate_key(cls):
        return Fernet.generate_key()
