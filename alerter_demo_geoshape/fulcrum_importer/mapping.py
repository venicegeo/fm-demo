def get_geojson(layer):
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


def get_layers():
    from .models import Layer

    layers = []
    for layer in Layer.objects.all():
        layers += [layer.layer_name]
    return layers
