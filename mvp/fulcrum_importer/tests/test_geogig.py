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

from django.test import TestCase, TransactionTestCase
from ..geogig import *
import inspect
from ..models import *
import copy
from django.db import IntegrityError, transaction


class GeogigTests(TestCase):
    def setUp(self):
        pass

    def test_create_delete_repo(self):
        test_repo = "test_repo"
        expected_repo_path = os.path.join(os.path.join(get_ogc_server().get('GEOGIG_DATASTORE_DIR'),
                                                       test_repo),
                                          '.geogig')
        create_geogig_repo(test_repo)
        self.assertTrue(os.path.exists(expected_repo_path))
        create_geogig_datastore(test_repo)
        for id, name in get_all_geogig_repos().iteritems():
            print("{}({})".format(id, name))
        # delete_geogig_repo(test_repo)
        # self.assertFalse(os.path.exists(expected_repo_path))
    #
    # def test_get_all_geogig_repo(self):
    #     repos = get_all_geogig_repos()
    #     for repo in repos:
    #         print repo
    #     #create_geogig_datastore(store_name="new_store")
    #     repos = get_all_geogig_repos()
    #     for repo in repos:
    #         print repo
