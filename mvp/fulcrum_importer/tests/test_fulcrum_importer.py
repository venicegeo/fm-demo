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
from ..fulcrum_importer import *
import inspect
from ..models import *
import copy
from django.db import IntegrityError, transaction


class FulcrumImporterTests(TestCase):
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

    def test_find_media_keys_from_urls(self):
        """

        Returns:Given a geojson containing a Fulcrum API media url,
        a json should be returned with those keys and types.
        This assumes that 'photos', 'videos', or 'audio' is in the media url.
        The test proves that even if the key is arbitrary the url will prove valid.

        """
        example_layer = Layer.objects.create(layer_name="example", layer_uid="unique")
        expected_keymap = {'pics': 'photos', 'vids': 'videos', 'sounds': 'audio'}
        bad_geojson = {'type': 'feature',
                       'properties': {'pics_url': '',
                                      'vids_url': 'https://api.fulcrumapp.com/api/v2/videos',
                                      'sounds_url': ''}}
        good_geojson = {'type': 'feature',
                        'properties': {'pics_url': 'https://api.fulcrumapp.com/api/v2/photos',
                                       'vids_url': 'https://api.fulcrumapp.com/api/v2/videos',
                                       'sounds_url': 'https://api.fulcrumapp.com/api/v2/audio'}}
        self.assertNotEqual(find_media_keys([bad_geojson], example_layer), expected_keymap)
        self.assertEqual(find_media_keys([good_geojson], example_layer), expected_keymap)

    def test_layer_media_keys_update(self):
        example_layer = Layer.objects.create(layer_name="example", layer_uid="unique")
        expected_keymap = {'pics': 'photos', 'vids': 'videos', 'sounds': 'audio'}
        bad_geojson = {'type': 'feature',
                       'properties': {'pics_url': '',
                                      'vids_url': 'https://api.fulcrumapp.com/api/v2/videos',
                                      'sounds_url': ''}}
        good_geojson = {'type': 'feature',
                        'properties': {'pics_url': 'https://api.fulcrumapp.com/api/v2/photos',
                                       'vids_url': 'https://api.fulcrumapp.com/api/v2/videos',
                                       'sounds_url': 'https://api.fulcrumapp.com/api/v2/audio'}}
        example_layer.layer_media_keys = find_media_keys([bad_geojson], example_layer)
        example_layer.save()
        self.assertNotEqual(example_layer.layer_media_keys, "{}")
        example_layer.layer_media_keys = find_media_keys([good_geojson], example_layer)
        example_layer.save()
        self.assertEqual(example_layer.layer_media_keys, expected_keymap)

    def test_feature_model_for_duplicates(self):
        example_layer = Layer.objects.create(layer_name="example", layer_uid="unique")
        first_feature = {
            "type": "Feature",
            "properties": {
                "fulcrum_id": "5daf7ab7-e257-48d1-b1e6-0bb049b49d98",
                "version": 1,
            }}
        second_feature = copy.deepcopy(first_feature)
        second_feature['properties']['version'] = 2
        feature1 = Feature.objects.create(layer=example_layer,
                                          feature_uid=first_feature.get('properties').get('fulcrum_id'),
                                          feature_version=first_feature.get('properties').get('version'),
                                          feature_data=json.dumps(first_feature))
        self.assertIsNotNone(feature1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Feature.objects.create(layer=example_layer,
                                       feature_uid=first_feature.get('properties').get('fulcrum_id'),
                                       feature_version=first_feature.get('properties').get('version'),
                                       feature_data=json.dumps(first_feature))
        feature2 = Feature.objects.create(layer=example_layer,
                                          feature_uid=second_feature.get('properties').get('fulcrum_id'),
                                          feature_version=second_feature.get('properties').get('version'),
                                          feature_data=json.dumps(second_feature))
        self.assertIsNotNone(feature2)

    def test_sort_features(self):
        unsorted_features = [{'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 2}},
                             {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 2}},
                             {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 1}},
                             {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 1}}]
        expected_sorted_by_version_features = [
            {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 1}},
            {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 1}},
            {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 2}},
            {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 2}}]
        expected_sorted_by_id_features = [{'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 2}},
                                          {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 1}},
                                          {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 2}},
                                          {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 1}}]
        expected_sorted_by_version_then_id = [
            {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 1}},
            {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 2}},
            {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 1}},
            {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 2}}]

        sorted_by_version_features = sort_features(unsorted_features, properties_key='version')
        self.assertEqual(sorted_by_version_features, expected_sorted_by_version_features)

        sorted_by_id_features = sort_features(unsorted_features, properties_key='id')
        self.assertEqual(expected_sorted_by_id_features, sorted_by_id_features)

        sorted_by_version_then_id = sort_features(sort_features(unsorted_features, properties_key='version')
                                                  , properties_key='id')
        self.assertEqual(sorted_by_version_then_id, expected_sorted_by_version_then_id)

    def test_get_duplicate_features(self):
        unsorted_features = [{'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 2}},
                             {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 2}},
                             {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 1}},
                             {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 1}},
                             {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f931ee7d5', 'version': 2}}]

        expected_unique_features = [{'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 1}},
                                    {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 1}},
                                    {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f931ee7d5', 'version': 2}}]

        expected_non_unique_features = [{'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d4', 'version': 2}},
                                        {'properties': {'id': 'cdec0e00-f511-44bf-a94e-165f930ce7d5', 'version': 2}}]

        unique_features, non_unique_features = get_duplicate_features(features=unsorted_features, properties_id='id')

        self.assertEqual(expected_unique_features, unique_features)
        self.assertEqual(expected_non_unique_features, non_unique_features)

    def test_table_exist(self):
        table_name = "test"
        self.assertFalse(table_exists(table=table_name))

        cur = connection.cursor()

        cur.execute("CREATE TABLE test(id);")

        self.assertTrue(table_exists(table=table_name))

    def test_features_to_file(self):
        test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        test_name = 'test_geojson.json'
        test_path = os.path.join(test_dir, test_name)
        test_features = {
                          "type": "Feature",
                          "geometry": {
                            "type": "Point",
                            "coordinates": [125.6, 10.1]
                          },
                          "properties": {
                            "name": "Dinagat Islands"
                          }
                        }
        expected_result = {"type": "FeatureCollection", "features": [test_features]}
        try:
            self.assertFalse(os.path.isfile(test_path))
        except AssertionError:
            os.remove(test_path)

        features_to_file(test_features, file_path=test_path)

        self.assertTrue(os.path.isfile(test_path))

        with open(test_path,'r') as test_file:
            imported_geojson = json.load(test_file)

        os.remove(test_path)

        print imported_geojson.get('type')

        self.assertEqual(expected_result, imported_geojson)
        self.assertFalse(os.path.isfile(test_path))

    def test_ogr2ogr_geojson_to_db(self):
        table_name = 'test'
        test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        test_name = 'test_geojson.json'
        test_path = os.path.join(test_dir, test_name)
        test_features = {
                          "type": "Feature",
                          "geometry": {
                            "type": "Point",
                            "coordinates": [125.6, 10.1]
                          },
                          "properties": {
                            "name": "Dinagat Islands"
                          }
                        }
        self.assertFalse(table_exists(table=table_name))

        geojson_file = features_to_file(test_features, file_path=test_path)
        self.assertTrue(os.path.isfile(geojson_file))

        ogr2ogr_geojson_to_db(geojson_file=geojson_file,
                              table=table_name)

        self.assertTrue(table_exists(table=table_name))
        os.remove(geojson_file)
