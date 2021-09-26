import os
from unittest import TestCase

from pdip.configuration.models import ApplicationConfig
from pdip.cryptography import CryptoService
from pdip.dependency.container import DependencyContainer


class TestCryptographyService(TestCase):
    def setUp(self):
        root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
        DependencyContainer.initialize_service(root_directory=root_directory)
        DependencyContainer.Instance.config_manager.set(ApplicationConfig, 'secret_key', CryptoService.generate_key().decode())

    def tearDown(self):
        pass

    def test_cryptography(self):
        crypto_service = DependencyContainer.Instance.get(CryptoService)
        test_data = 'data'
        encrypted_data = crypto_service.encrypt(data=test_data)
        decrypted_data = crypto_service.decrypt(data=encrypted_data)
        assert test_data == decrypted_data
