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
from ..djfulcrum import *
from ..models import *
from ..fetch_workflow import PzWorkflow

class ViewerTests(TestCase):

    def setUp(self):
        pass

    def test_status(self):
        print "Testing status"
        pz_workflow = PzWorkflow("http://pz-workflow.cf.piazzageo.io")
        status = pz_workflow.status()
        self.assertEqual(status, 200)

    def test_request_action(self):
        print "Testing action"
        pz_workflow = PzWorkflow("http://pz-workflow.cf.piazzageo.io")
        bad_request = json.dumps({'type': 'event', 'data': {}, 'action': 'badAction'})
        request = pz_workflow.request(bad_request)
        self.assertIsNone(request)

    def test_find_by_data(self):
        print "Testing find_by_data"
        pz_workflow = PzWorkflow("http://pz-workflow.cf.piazzageo.io")
        user_request = {'type': 'event', 'action': 'get', 'data': {'type': 'sometype', 'date': 'somedate', 'data': {'filename': 'filename', 'severity': 44, 'code': 'somecode'}}}
        items = [
                {'type': 'sometype2', 'date': 'somedate2', 'data': {'filename': 'filename2', 'severity': 3, 'code': 'somecode2'}},
                {'type': 'sometype', 'date': 'somedate', 'data': {'filename': 'filename', 'severity': 44, 'code': 'somecode'}},
                {'type': 'sometype3', 'date': 'somedate3', 'data': {'filename': 'filename3', 'severity': 22, 'code': 'somecode3'}}
                ]
        self.assertEqual(pz_workflow.find_by_data(items, user_request), user_request["data"])

    def test_find_by_id(self):
        print "Testing find_by_id"
        pz_workflow = PzWorkflow("http://pz-workflow.cf.piazzageo.io")
        user_request = {'type': 'event', 'action': 'get', 'data': {'id': 'E23', 'type': 'sometype', 'date': 'somedate', 'data': {'filename': 'filename', 'severity': 44, 'code': 'somecode'}}}
        items = [
                {'id': 'E24','type': 'sometype2', 'date': 'somedate2', 'data': {'filename': 'filename2', 'severity': 3, 'code': 'somecode2'}},
                {'id': 'E23', 'type': 'sometype', 'date': 'somedate', 'data': {'filename': 'filename', 'severity': 44, 'code': 'somecode'}},
                {'id': 'E25','type': 'sometype3', 'date': 'somedate3', 'data': {'filename': 'filename3', 'severity': 22, 'code': 'somecode3'}}
                ]
        self.assertEqual(pz_workflow.find_by_data(items, user_request), user_request["data"])

    def test_bad_get_id(self):
        print "Testing get by bad ID"
        pz_workflow = PzWorkflow("http://pz-workflow.cf.piazzageo.io")
        bad_request = {'type': 'event', 'data': {'id': 'badID'}, 'action': 'get'}
        request = pz_workflow.request(json.dumps(bad_request))
        self.assertIsNone(request)

    def test_bad_get_data(self):
        print "Testing get by bad data"
        pz_workflow = PzWorkflow("http://pz-workflow.cf.piazzageo.io")
        bad_request = json.dumps({'type': 'event', 'data': {'type': 'sometype', 'date': 'somedate', 'data': {'filename': 'filename', 'severity': 44, 'code': 'somecode'}}, 'action':'get'})
        request = pz_workflow.request(bad_request)
        self.assertIsNone(request)
