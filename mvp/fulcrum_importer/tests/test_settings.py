# Copyright 2016, RadiantBlue Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import

from django.test import TestCase
from django.conf import settings


class SettingsTests(TestCase):
    def setUp(self):
        pass

    def test_verify_ssl(self):
        ssl_verify = getattr(settings, 'SSL_VERIFY', True)
        try:
            settings.SSL_VERIFY
            ssl_verify_exists = True
        except AttributeError:
            ssl_verify_exists = False
        if ssl_verify_exists:
            print("SSL_VERIFY:{}".format(ssl_verify))
            self.assertEqual(ssl_verify, settings.SSL_VERIFY)
        else:
            print("SSL_VERIFY setting not defined. Defaulting to {}.".format(ssl_verify))
            self.assertTrue(ssl_verify)
