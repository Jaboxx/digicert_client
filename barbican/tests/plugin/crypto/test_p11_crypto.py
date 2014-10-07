# Copyright (c) 2013-2014 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

from barbican.model import models
from barbican.plugin.crypto import crypto as plugin_import
from barbican.plugin.crypto import p11_crypto
from barbican.tests import utils


class WhenTestingP11CryptoPlugin(utils.BaseTestCase):

    def setUp(self):
        super(WhenTestingP11CryptoPlugin, self).setUp()

        self.p11_mock = mock.MagicMock(CKR_OK=0, CKF_RW_SESSION='RW',
                                       name='PyKCS11 mock')
        self.patcher = mock.patch('barbican.plugin.crypto.p11_crypto.PyKCS11',
                                  new=self.p11_mock)
        self.patcher.start()
        self.pkcs11 = self.p11_mock.PyKCS11Lib()
        self.p11_mock.PyKCS11Error.return_value = Exception()
        self.pkcs11.lib.C_Initialize.return_value = self.p11_mock.CKR_OK
        self.pkcs11.lib.C_GenerateKey.return_value = self.p11_mock.CKR_OK
        self.cfg_mock = mock.MagicMock(name='config mock')
        self.plugin = p11_crypto.P11CryptoPlugin(self.cfg_mock)
        self.session = self.pkcs11.openSession()

    def tearDown(self):
        super(WhenTestingP11CryptoPlugin, self).tearDown()
        self.patcher.stop()

    def test_generate_calls_generate_random(self):
        with mock.patch.object(self.plugin, 'encrypt') as encrypt_mock:
            # patch out the encrypt call since it is irrelevant in this test
            encrypt_mock.return_value = None
            self.session.generateRandom.return_value = [1, 2, 3, 4, 5, 6, 7,
                                                        8, 9, 10, 11, 12, 13,
                                                        14, 15, 16]
            secret = models.Secret()
            secret.bit_length = 128
            secret.algorithm = "AES"
            generate_dto = plugin_import.GenerateDTO(
                secret.algorithm,
                secret.bit_length,
                None, None)
            self.plugin.generate_symmetric(
                generate_dto,
                mock.MagicMock(),
                mock.MagicMock()
            )
            self.session.generateRandom.assert_called_twice_with(16)

    def test_generate_errors_when_rand_length_is_not_as_requested(self):
        self.session.generateRandom.return_value = [1, 2, 3, 4, 5, 6, 7]
        secret = models.Secret()
        secret.bit_length = 192
        secret.algorithm = "AES"
        generate_dto = plugin_import.GenerateDTO(
            secret.algorithm,
            secret.bit_length,
            None, None)
        self.assertRaises(
            p11_crypto.P11CryptoPluginException,
            self.plugin.generate_symmetric,
            generate_dto,
            mock.MagicMock(),
            mock.MagicMock()
        )

    def test_raises_error_with_no_library_path(self):
        m = mock.MagicMock()
        m.p11_crypto_plugin = mock.MagicMock(library_path=None)
        self.assertRaises(
            ValueError,
            p11_crypto.P11CryptoPlugin,
            m,
        )

    def test_raises_error_with_bad_library_path(self):
        m = mock.MagicMock()
        self.pkcs11.lib.C_Initialize.return_value = 12345
        m.p11_crypto_plugin = mock.MagicMock(library_path="/dev/null")

        pykcs11error = Exception
        self.assertRaises(
            pykcs11error,
            p11_crypto.P11CryptoPlugin,
            m,
        )

    def test_get_key_handle_with_two_keys(self):
        self.session.findObjects.return_value = ['key1', 'key2']
        self.assertRaises(
            p11_crypto.P11CryptoPluginKeyException,
            self.plugin._get_key_handle,
            'mylabel',
        )

    def test_get_key_handle_with_one_key(self):
        key = 'key1'
        self.session.findObjects.return_value = [key]
        key_label = self.plugin._get_key_handle('mylabel')
        self.assertEqual(key, key_label)

    def test_get_key_handle_with_no_keys(self):
        self.session.findObjects.return_value = []
        result = self.plugin._get_key_handle('mylabel')
        self.assertIsNone(result)

    def test_generate_iv_calls_generate_random(self):
        self.session.generateRandom.return_value = [1, 2, 3, 4, 5, 6, 7,
                                                    8, 9, 10, 11, 12, 13,
                                                    14, 15, 16]
        iv = self.plugin._generate_iv()
        self.assertEqual(len(iv), self.plugin.block_size)
        self.session.generateRandom.assert_called_once_with(
            self.plugin.block_size)

    def test_generate_iv_with_invalid_response_size(self):
        self.session.generateRandom.return_value = [1, 2, 3, 4, 5, 6, 7]
        self.assertRaises(
            p11_crypto.P11CryptoPluginException,
            self.plugin._generate_iv,
        )

    def test_build_gcm_params(self):
        class GCMMock(object):
            def __init__(self):
                self.pIv = None
                self.ulIvLen = None
                self.ulIvBits = None
                self.ulTagBits = None

        self.p11_mock.LowLevel.CK_AES_GCM_PARAMS.return_value = GCMMock()
        iv = b'sixteen_byte_iv_'
        gcm = self.plugin._build_gcm_params(iv)
        self.assertEqual(iv, gcm.pIv)
        self.assertEqual(len(iv), gcm.ulIvLen)
        self.assertEqual(len(iv) * 8, gcm.ulIvBits)
        self.assertEqual(128, gcm.ulIvBits)

    def test_encrypt(self):
        payload = 'encrypt me!!'
        self.session.generateRandom.return_value = [1, 2, 3, 4, 5, 6, 7,
                                                    8, 9, 10, 11, 12, 13,
                                                    14, 15, 16]
        mech = mock.MagicMock()
        self.p11_mock.Mechanism.return_value = mech
        self.session.encrypt.return_value = [1, 2, 3, 4, 5]
        encrypt_dto = plugin_import.EncryptDTO(payload)
        with mock.patch.object(self.plugin, '_unwrap_key') as unwrap_key_mock:
            unwrap_key_mock.return_value = 'unwrapped_key'
            response_dto = self.plugin.encrypt(encrypt_dto,
                                               mock.MagicMock(),
                                               mock.MagicMock())

            self.session.encrypt.assert_called_once_with('unwrapped_key',
                                                         payload,
                                                         mech)
            self.assertEqual(b'\x01\x02\x03\x04\x05', response_dto.cypher_text)
            self.assertEqual('{"iv": "AQIDBAUGBwgJCgsMDQ4PEA=="}',
                             response_dto.kek_meta_extended)

    def test_decrypt(self):
        ct = mock.MagicMock()
        self.session.decrypt.return_value = [100, 101, 102, 103]
        mech = mock.MagicMock()
        self.p11_mock.Mechanism.return_value = mech
        kek_meta_extended = '{"iv": "AQIDBAUGBwgJCgsMDQ4PEA=="}'
        decrypt_dto = plugin_import.DecryptDTO(ct)
        with mock.patch.object(self.plugin, '_unwrap_key') as unwrap_key_mock:
            unwrap_key_mock.return_value = 'unwrapped_key'
            payload = self.plugin.decrypt(decrypt_dto,
                                          mock.MagicMock(),
                                          kek_meta_extended,
                                          mock.MagicMock())
            self.assertTrue(self.p11_mock.Mechanism.called)
            self.session.decrypt.assert_called_once_with('unwrapped_key',
                                                         ct,
                                                         mech)
            self.assertEqual(b'defg', payload)

    def test_bind_kek_metadata_without_existing_key(self):
        self.session.findObjects.return_value = []  # no existing key
        self.pkcs11.lib.C_GenerateKey.return_value = self.p11_mock.CKR_OK

        self.plugin.bind_kek_metadata(mock.MagicMock())

        self.assertTrue(self.session._template2ckattrlist.called)
        self.assertTrue(self.p11_mock.LowLevel.CK_MECHANISM.called)

    def test_bind_kek_metadata_with_existing_key(self):
        self.session.findObjects.return_value = ['key1']  # one key

        dto_mock = mock.MagicMock()
        self.assertEqual(self.plugin.bind_kek_metadata(dto_mock), dto_mock)

    def test_generate_asymmetric_raises_error(self):
        self.assertRaises(NotImplementedError,
                          self.plugin.generate_asymmetric,
                          mock.MagicMock(),
                          mock.MagicMock(),
                          mock.MagicMock())

    def test_supports_encrypt_decrypt(self):
        self.assertTrue(
            self.plugin.supports(
                plugin_import.PluginSupportTypes.ENCRYPT_DECRYPT
            )
        )

    def test_supports_symmetric_key_generation(self):
        self.assertTrue(
            self.plugin.supports(
                plugin_import.PluginSupportTypes.SYMMETRIC_KEY_GENERATION
            )
        )

    def test_does_not_support_asymmetric_key_generation(self):
        self.assertFalse(
            self.plugin.supports(
                plugin_import.PluginSupportTypes.ASYMMETRIC_KEY_GENERATION
            )
        )

    def test_does_not_support_unknown_type(self):
        self.assertFalse(
            self.plugin.supports("SOMETHING_RANDOM")
        )
