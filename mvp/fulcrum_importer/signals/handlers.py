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

from django.db.models.signals import post_save
from django.dispatch import receiver
from fulcrum_importer.models import Feature
from django.core.cache import cache
from fulcrum_importer.mapping import get_geojson


@receiver(post_save, sender=Feature)
def push_features(sender, instance, **kwargs):
    print("UPDATING FEATURES!")
    layer = instance.layer
    updated_features = cache.get("updated_features")
    if not updated_features:
        updated_features = {}
    updated_features[layer.layer_name] = get_geojson(layer.layer_name)
    cache.set("updated_features",updated_features)