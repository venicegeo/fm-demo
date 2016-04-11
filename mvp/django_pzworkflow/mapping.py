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


def get_geojson(layer):
    """

    Args:
        layer: Converts the feature data for a layer to geojson.

    Returns:

    """
    from django.core.exceptions import ObjectDoesNotExist
    from .models import Layer, Feature
    import json
    import time
    from dateutil import parser

    json_features = []
    try:
        layer = Layer.objects.get(layer_name=layer)
        features = Feature.objects.filter(layer=layer)
    except ObjectDoesNotExist:
        return None
    for feature in features:
        json_feature = json.loads(feature.feature_data)
        if json_feature.get('properties').get('system_updated_at'):
            date = parser.parse(json_feature.get('properties').get('system_updated_at'))
        elif json_feature.get('properties').get('updated_at'):
            date = parser.parse(json_feature.get('properties').get('updated_at'))
        elif json_feature.get('properties').get('created_at'):
            date = parser.parse(json_feature.get('properties').get('created_at'))
        else: date = None
        if date:
            json_feature["properties"]["time"] = time.mktime(date.timetuple())
        json_features += [json_feature]

    feature_collection = {"type":"FeatureCollection","features": json_features}
    return json.dumps(feature_collection)


def get_layer_names():
    """

    Returns: The layers as a dict.

    """
    from .models import Layer

    layers = {}
    for layer in Layer.objects.all():
        layers[layer.layer_name] = None
    return layers


def get_pz_events():
    """

    Returns: A dict of pz-events

    """
    from .models import PzEvents
    import json
    pz_models = {}
    events = PzEvents.objects.all()
    if events:
        for event in events:
            event_info = {"event_data": json.loads(event.event_data)}
            if event.event_lat and event.event_lng:
                event_info["coordinates"] = [event.event_lng, event.event_lat]
            pz_models[event.event_id] = event_info

    return pz_models


def get_pz_triggers():
    """

    Returns: An array of dicts. Each dict corresponds to an trigger.
    The dict key is trigger_id, the value is trigger_data

    """
    from .models import PzTriggers
    import json
    pz_models = {}
    triggers = PzTriggers.objects.all()
    if triggers:
        for trigger in triggers:
            pz_models[trigger.trigger_id] = {"trigger_data": json.loads(trigger.trigger_data)}
    return pz_models


def get_pz_features():
    """

    Returns: An array of geojson features

    """
    from .models import PzFeatures
    import json
    pz_features = []
    features = PzFeatures.objects.all()
    if features:
        for feature in features:
            pz_features.append(json.loads(feature.feature))
    return pz_features
