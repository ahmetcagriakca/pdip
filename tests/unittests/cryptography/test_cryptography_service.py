import sys
from unittest import TestCase

from injector import Binder

from pdip.base import Pdi
from pdip.configuration.models.application import ApplicationConfig
from pdip.cryptography import CryptoService


class TestCryptographyService(TestCase):
    def setUp(self):
        try:
            self.pdi = Pdi(configurations=[self.generate_key])
        except:
            self.tearDown()
            raise

    def tearDown(self):
        if hasattr(self, 'pdi') and self.pdi is not None:
            self.pdi.cleanup()
            del self.pdi
        return super().tearDown()

    def generate_key(self, binder: Binder):
        key = CryptoService.generate_key().decode()
        application_config = binder.injector.get(ApplicationConfig)
        application_config.secret_key = key
        # self.pdi.set_secret_key(key=key)

    def test_cryptography(self):
        test_data = 'data'
        crypto_service = self.pdi.get(CryptoService)
        encrypted_data = crypto_service.encrypt(data=test_data)
        decrypted_data = crypto_service.decrypt(data=encrypted_data)
        assert test_data == decrypted_data
