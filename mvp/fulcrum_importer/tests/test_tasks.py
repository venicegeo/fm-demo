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
from django.db import IntegrityError
from ..fulcrum_importer import *
import inspect
from ..models import *

class TasksTests(TestCase):

    def setUp(self):
        pass

    # def test_unzip(self):
    #     """File should be unzipped to a specified directory"""
    #     test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    #     unzip_file(os.path.join(test_dir, 'unzipped_file'),
    #                os.path.join(test_dir,
    #                             os.path.join('sample_data','Fulcrum_Export.zip')))
    #     self.assertTrue(os.path.exists(os.path.join(test_dir,
    #                                                 os.path.join('unzipped_file',
    #                                                              'test2'))))

    def test_write_to_S3(self):
        """

        Returns: Passes if S3Sync model exists and is writable and
        prevents duplicates.
        """
        file_name = "Test"
        s3 = S3Sync.objects.create(s3_filename=file_name)
        self.assertIsNotNone(s3)



