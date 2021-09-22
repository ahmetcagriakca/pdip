from cryptography.fernet import Fernet
from injector import inject
from ..dependency.scopes import IScoped
from ..configuration.models import ApplicationConfig


class CryptoService(IScoped):
    @inject
    def __init__(self, application_config: ApplicationConfig):
        self.application_config = application_config

    def decrypt_code(self, crypted_text):
        secret_key = self.application_config.secret_key.encode()
        f = Fernet(secret_key)
        return f.decrypt(crypted_text)

    def encrypt_code(self, decrypted_text):
        secret_key = self.application_config.secret_key.encode()
        f = Fernet(secret_key)
        return f.encrypt(decrypted_text)
