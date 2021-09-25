import os
from unittest import TestCase

from pdi.configuration.models import ApplicationConfig
from pdi.cryptography import CryptoService
from pdi.dependency.container import DependencyContainer


class TestCryptographyService(TestCase):
    def setUp(self):
        root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
        DependencyContainer.initialize_service(root_directory=root_directory)
        DependencyContainer.Instance.config_manager.set(ApplicationConfig, 'secret_key', CryptoService.generate_key().decode())
        application_config = DependencyContainer.Instance.config_manager.get(ApplicationConfig)
        DependencyContainer.Instance.binder.bind(interface=ApplicationConfig, to=application_config)

    def tearDown(self):
        pass

    @classmethod
    def process_method(cls, sub_process_id, data):
        print(f"{sub_process_id}-{data}")
        return data

    def test_cryptography(self):
        crypto_service = DependencyContainer.Instance.get(CryptoService)
        test_data = 'data'
        encrypted_data = crypto_service.encrypt(data=test_data)
        decrypted_data = crypto_service.decrypt(data=encrypted_data)
        assert test_data == decrypted_data
