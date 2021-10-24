import sys
from unittest import TestCase
from pdip.base import Pdi
from pdip.configuration.models.application import ApplicationConfig

from pdip.cryptography import CryptoService
from pdip.dependency.container import DependencyContainer


class TestCryptographyService(TestCase):
    def setUp(self):
        self.pdi = Pdi(configurations=[self.generate_key])
        self.crypto_service = self.pdi.get(CryptoService)

    def tearDown(self):
        modules = [y for y in sys.modules if 'pdip' in y]
        for module in modules:
            del module
        return super().tearDown()

    def generate_key(self, binder):
        key = CryptoService.generate_key().decode()
        DependencyContainer.Instance.config_manager.set(ApplicationConfig, 'secret_key', key)

    def test_cryptography(self):
        test_data = 'data'
        encrypted_data = self.crypto_service.encrypt(data=test_data)
        decrypted_data = self.crypto_service.decrypt(data=encrypted_data)
        assert test_data == decrypted_data
