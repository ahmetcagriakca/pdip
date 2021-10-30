import sys
from unittest import TestCase

from injector import Binder

from pdip.base import Pdi
from pdip.configuration.models.application import ApplicationConfig
from pdip.cryptography import CryptoService


class TestCryptographyService(TestCase):
    def setUp(self):
        self.pdi = Pdi(configurations=[self.generate_key])
        self.crypto_service = self.pdi.get(CryptoService)

    def tearDown(self):
        modules = [y for y in sys.modules if 'pdip' in y]
        for module in modules:
            del module
        return super().tearDown()

    def generate_key(self, binder: Binder):
        key = CryptoService.generate_key().decode()
        application_config = binder.injector.get(ApplicationConfig)
        application_config.secret_key = key
        # self.pdi.set_secret_key(key=key)

    def test_cryptography(self):
        test_data = 'data'
        encrypted_data = self.crypto_service.encrypt(data=test_data)
        decrypted_data = self.crypto_service.decrypt(data=encrypted_data)
        assert test_data == decrypted_data
