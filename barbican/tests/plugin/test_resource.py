# Copyright (c) 2014 Red Hat, Inc.
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

import barbican.model.repositories as repo
from barbican.plugin.interface import secret_store
from barbican.plugin import resources
import mock
import testtools


class WhenTestingPluginResource(testtools.TestCase):

    def setUp(self):
        super(WhenTestingPluginResource, self).setUp()
        self.plugin_resource = resources
        self.spec = {'algorithm': 'RSA',
                     'bit_length': 1024,
                     'passphrase': 'changeit'
                     }
        self.content_type = 'application/octet-stream'
        self.tenant_model = mock.MagicMock()
        asymmetric_meta_dto = secret_store.AsymmetricKeyMetadataDTO()
        # Mock plug-in
        self.generate_plugin = mock.MagicMock()
        self.generate_plugin.generate_asymmetric_key.return_value =\
            asymmetric_meta_dto

        gen_plugin_config = {
            'return_value.get_plugin_generate.return_value':
            self.generate_plugin
        }

        self.gen_plugin_patcher = mock.patch(
            'barbican.plugin.interface.secret_store'
            '.SecretStorePluginManager',
            **gen_plugin_config
        )
        self.gen_plugin_patcher.start()

        tenant_repo = mock.MagicMock()
        secret_repo = mock.MagicMock()
        secret_repo.create_from.return_value = None
        container_repo = mock.MagicMock()
        container_repo.create_from.return_value = None
        container_secret_repo = mock.MagicMock()
        container_secret_repo.create_from.return_value = None
        tenant_secret_repo = mock.MagicMock()
        tenant_secret_repo.create_from.return_value = None
        secret_meta_repo = mock.MagicMock()
        secret_meta_repo.create_from.return_value = None

        self.repos = repo.Repositories(container_repo=container_repo,
                                       container_secret_repo=
                                       container_secret_repo,
                                       tenant_repo=tenant_repo,
                                       secret_repo=secret_repo,
                                       tenant_secret_repo=tenant_secret_repo,
                                       secret_meta_repo=secret_meta_repo)

    def tearDown(self):
        super(WhenTestingPluginResource, self).tearDown()

    def test_generate_asymmetric_with_passphrase(self):
        """test asymmetric secret generation with passphrase."""
        secret_container = \
            self.plugin_resource.\
            generate_asymmetric_secret(self.spec,
                                       self.content_type,
                                       self.tenant_model,
                                       self.repos)

        self.assertEqual("rsa", secret_container.type)
        self.assertEqual(self.generate_plugin.
                         generate_asymmetric_key.call_count, 1)
        self.assertEqual(self.repos.container_repo.
                         create_from.call_count, 1)
        self.assertEqual(self.repos.container_secret_repo.
                         create_from.call_count, 3)

    def test_generate_asymmetric_without_passphrase(self):
        """test asymmetric secret generation without passphrase."""

        del self.spec['passphrase']
        secret_container =\
            self.plugin_resource.\
            generate_asymmetric_secret(self.spec,
                                       self.content_type,
                                       self.tenant_model,
                                       self.repos)

        self.assertEqual("rsa", secret_container.type)
        self.assertEqual(self.generate_plugin.generate_asymmetric_key.
                         call_count, 1)
        self.assertEqual(self.repos.container_repo.create_from.
                         call_count, 1)
        self.assertEqual(self.repos.container_secret_repo.create_from.
                         call_count, 2)
