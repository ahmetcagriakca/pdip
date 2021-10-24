import os
from unittest import TestCase
from pdip import Pdi

from pdip.cryptography import CryptoService


class TestCryptographyService(TestCase):
    def setUp(self):
        self.pdi = Pdi()
        self.pdi.set_secret_key(key=CryptoService.generate_key().decode())

    def tearDown(self):
        pass

    def test_cryptography(self):
        crypto_service = self.pdi.get(CryptoService)
        test_data = 'data'
        encrypted_data = crypto_service.encrypt(data=test_data)
        decrypted_data = crypto_service.decrypt(data=encrypted_data)
        assert test_data == decrypted_data
