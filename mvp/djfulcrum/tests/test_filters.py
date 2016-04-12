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
from ..filters.geospatial_filter import *
from ..filters.phone_number_filter import *
from ..filters.run_filters import filter
import os
import json
from shapely.geometry import shape

class FilterTests(TestCase):

    def setUp(self):
        pass


    def test_get_boundary_features(self):
        """
        Test boundary feature creation
        boundary features should have on item of MultiPolygon type
        """
        boundary_features = get_boundary_features()
        self.assertEqual(len(boundary_features), 1)
        self.assertEqual(boundary_features[0].geom_type, 'MultiPolygon')


    def test_check_geometry(self):
        """
        Test geometry checker
        Coordinates in US should return true. Coordinates outside the us should return false
        """
        boundary_features = get_boundary_features()
        us_in = [-82.96875, 37.996162679728116]
        self.assertTrue(check_geometry(us_in, boundary_features))
        us_out = [-105.1171875, 4.565473550710278]
        self.assertFalse(check_geometry(us_out, boundary_features))


    def test_full_geometry_filter(self):
        """
        Test geometry filter on geojson
        Us_test_features.geojson should be filtered completely, no passed features, five failed features.
        Non_us_test_features.geojson should not be filtered out, five passed features, no failed features.
        """
        boundary_features = get_boundary_features()
        with open(os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'us_test_features.geojson')) as testfile:
            features = json.load(testfile)
            testfile.close()

        filtered = filter_spatial_features(features, boundary_features)
        fail_count = len(filtered.get('failed').get('features'))
        pass_count = len(filtered.get('passed').get('features'))
        self.assertEqual(fail_count,5)
        self.assertEqual(pass_count,0)

        with open(os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'non_us_test_features.geojson')) as testfile2:
            features2 = json.load(testfile2)
            testfile2.close()

        filtered2 = filter_spatial_features(features2, boundary_features)
        fail_count2 = len(filtered2.get('failed').get('features'))
        pass_count2 = len(filtered2.get('passed').get('features'))
        self.assertEqual(fail_count2, 0)
        self.assertEqual(pass_count2, 5)


    def test_get_area_codes(self):
        """
        Test area code return
        get_area_codes should return an array of 321 area codes
        """
        area_codes = get_area_codes()
        self.assertEqual(len(area_codes), 321)


    def test_check_numbers(self):
        """
        Test number checker
        Phone numbers in correct phone number format and containing a US area code should return true, others should return false
        """
        us_number1 = '443-908-8888'
        us_number2 = '443.908.8888'
        us_number3 = '(443)908-8888'
        us_number4 = '1-(443)-908-8888'
        non_us_number1 = '4439088888'
        non_us_number2 = '888-908-8888'
        non_us_number3 = '45443-908-8888'
        non_us_number4 = '443-8t8-8888'

        self.assertTrue(check_numbers(us_number1))
        self.assertTrue(check_numbers(us_number2))
        self.assertTrue(check_numbers(us_number3))
        self.assertTrue(check_numbers(us_number4))
        self.assertFalse(check_numbers(non_us_number1))
        self.assertFalse(check_numbers(non_us_number2))
        self.assertFalse(check_numbers(non_us_number3))
        self.assertFalse(check_numbers(non_us_number4))

    def test_full_phone_number_filters(self):
        """
        Test phone number in geojson filter
        Half the features should be filtered out.
        Passed should contain four features.
        Failed should contain four features.
        """
        my_features = {
          "type": "FeatureCollection",
          "features": [
            {
              "type": "Feature",
              "properties": {"number": '443.908.8888'},
              "geometry": {
                "type": "Point",
                "coordinates": [
                  -137.8125,
                  45.82879925192134
                ]
              }
            },
            {
              "type": "Feature",
              "properties": {"number": '443-908-8888'},
              "geometry": {
                "type": "Point",
                "coordinates": [
                  -85.078125,
                  12.21118019150401
                ]
              }
            },
            {
              "type": "Feature",
              "properties": {"number": '(443)908-8888'},
              "geometry": {
                "type": "Point",
                "coordinates": [
                  -56.42578125,
                  3.6888551431470478
                ]
              }
            },
              {
              "type": "Feature",
              "properties": {"number": '1-(443)-908-8888'},
              "geometry": {
                "type": "Point",
                "coordinates": [
                  -56.42578125,
                  3.6888551431470478
                ]
              }
            },
            {
              "type": "Feature",
              "properties": {"number": '4439088888'},
              "geometry": {
                "type": "Point",
                "coordinates": [
                  -137.8125,
                  45.82879925192134
                ]
              }
            },
            {
              "type": "Feature",
              "properties": {"number": '888-908-8888'},
              "geometry": {
                "type": "Point",
                "coordinates": [
                  -85.078125,
                  12.21118019150401
                ]
              }
            },
            {
              "type": "Feature",
              "properties": {"number": '45443-908-8888'},
              "geometry": {
                "type": "Point",
                "coordinates": [
                  -56.42578125,
                  3.6888551431470478
                ]
              }
            },
              {
              "type": "Feature",
              "properties": {"number": '443-9t8-8888'},
              "geometry": {
                "type": "Point",
                "coordinates": [
                  -56.42578125,
                  3.6888551431470478
                ]
              }
            }
          ]
        }
        filtered_features = filter_number_features(my_features)
        self.assertEqual(len(filtered_features.get('passed').get('features')), 4)
        self.assertEqual(len(filtered_features.get('failed').get('features')), 4)


    def test_run_filters(self):
        """
        Test complete filtering process.
        Non_us_test_features should have 3 features after filtering. (US phone numbers found)
        Us_test_features should have 0 features after filtering. (Features located in the US)
        """
        with open(os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'non_us_test_features.geojson')) as testfile:
            features = json.load(testfile)
            testfile.close()
        filtered_results, filtered_results_count = filter(features)
        self.assertIsNotNone(filtered_results)
        self.assertEqual(filtered_results_count, 3)

        with open(os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'us_test_features.geojson')) as testfile2:
            features2 = json.load(testfile2)
            testfile2.close()
        filtered_results2, filtered_results_count2 = filter(features2)
        self.assertIsNone(filtered_results2)
        self.assertEqual(filtered_results_count2, 0)

    # def test_filter_previous(self):
    #     """
    #     Test filter previously unfiltered features.
    #     Non_us_test_features should have 3 features after filtering. (US phone numbers found)
    #     Us_test_features should have 0 features after filtering. (Features located in the US)
    #     """
    #     with open(os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'non_us_test_features.geojson')) as testfile:
    #         features = json.load(testfile)
    #         testfile.close()
    #     filtered_results, filtered_results_count = filter(features)
    #     self.assertIsNotNone(filtered_results)
    #     self.assertEqual(filtered_results_count, 3)
    #
    #     with open(os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'us_test_features.geojson')) as testfile2:
    #         features2 = json.load(testfile2)
    #         testfile2.close()
    #     filtered_results2, filtered_results_count2 = filter(features2)
    #     self.assertIsNone(filtered_results2)
    #     self.assertEqual(filtered_results_count2, 0)
