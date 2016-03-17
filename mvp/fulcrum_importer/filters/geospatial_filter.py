import os
from shapely.geometry import Point, MultiPolygon, Polygon, shape
from types import *
import json
import copy


def filter(input):

        boundary_features = get_boundary_features()
        passed_failed = filter_spatial_features(input, boundary_features)
        return passed_failed

def filter_spatial_features(input_features, boundary_features):
    if type(input_features) is DictType:
        if input_features.get("features"):
            return iterate_geojson(input_features, boundary_features)
        else:
            return iterate_json(input_features, boundary_features)

    elif type(input_features) is ListType:
        return iterate_array(input_features, boundary_features)
    else:
        return None

def iterate_geojson(input_features, boundary_features):
    passed = []
    failed = []
    for feature in input_features.get("features"):
        coords = feature.get('geometry').get('coordinates')
        if coords:
            if check_geometry(coords, boundary_features):
                failed.append(feature)
            else:
                passed.append(feature)
    passed_features = copy.deepcopy(input_features)
    passed_features['features'] = []
    passed_features['features'] = passed
    failed_features = input_features
    failed_features['features'] = []
    failed_features['features'] = failed
    return {'passed': passed_features, 'failed': failed_features}

def iterate_json(input_features, boundary_features):
    passed = []
    failed = []
    coords = None
    if input_features.get('lat') and input_features.get('lon'):
        coords = [input_features.get('lon'), input_features.get('lat')]
    elif input_features.get('latitude') and input_features.get('longitude'):
        coords = [input_features.get('longitude'), input_features.get('latitude')]
    if coords:
        if check_geometry(coords, boundary_features):
            failed.append(input_features)
        else:
            passed.append(input_features)
    else:
        passed.append(input_features)

    return {'passed': passed, 'failed': failed}

def iterate_array(input_features, boundary_features):
    passed = []
    failed = []
    for feature in input_features:
        coords = None
        if input_features[feature].get('latitude') and input_features[feature].get('longitude'):
            coords = [input_features[feature].get('longitude'), input_features[feature].get('latitude')]
        elif input_features[feature].get('lat') and input_features[feature].get('lon'):
            coords = [input_features[feature].get('lon'), input_features[feature].get('lat')]
        if coords:
            if check_geometry(coords, boundary_features):
                failed.append(input_features[feature])
            else:
                passed.append(input_features[feature])
    return {'passed': passed, 'failed': failed}

def check_geometry(coords, boundary_features):
    point = Point(coords[0], coords[1])
    for index, boundary in enumerate(boundary_features):
        if boundary_features[index].contains(point):
            return True
    return False

def get_boundary_features():
    polygons = []
    filepath = os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'boundary_polygons')
    files = os.listdir(filepath)
    for file in files:
        if file.endswith('.geojson'):
            with open(os.path.join(filepath, file)) as file_data:
                try:
                    data = json.load(file_data)
                    #data = coords_array_to_tuple(data)
                    geometry = shape(data.get('geometry')).buffer(0.1)
                    if geometry.geom_type is 'MultiPolygon' or geometry.geom_type is 'Polygon':
                        polygons.append(geometry)
                    file_data.close()
                except ValueError:
                    print "Error getting polygon data"
                    file_data.close()
    return polygons

# def coords_array_to_tuple(feature):
#     for ind, val in enumerate(feature.get('geometry').get('coordinates')):
#         for ind2, val2 in enumerate(val):
#             for ind3, val3 in enumerate(val2):
#                 feature['geometry']['coordinates'][ind][ind2][ind3] = tuple(val3)
#             feature['geometry']['coordinates'][ind][ind2] = tuple(val2)
#         feature['geometry']['coordinates'][ind] = tuple(val)
#     return feature


def main():
    boundary_features = get_boundary_features()
    # print boundary_features
    # us_in = [-82.96875, 37.996162679728116]
    # print check_geometry(us_in, boundary_features)
    # us_out = [-105.1171875, 4.565473550710278]
    # print check_geometry(us_out, boundary_features)
    # aus_buffer_in = [120.06683349609374, -19.91267470522604]
    # print check_geometry(aus_buffer_in, boundary_features)
    # aus_in_ = [120.46234130859376,-20.035289711352377]
    # print check_geometry(aus_in_, boundary_features)
    # aus_out = [109.874267578125, -15.050905707724771]
    # print check_geometry(aus_out, boundary_features)
    #
    with open(os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'us_test_features.geojson')) as testfile:
        features = json.load(testfile)
        testfile.close()

    filtered = filter_features(features, boundary_features)
    print filtered
    print len(filtered.get('failed').get('features'))

    with open(os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'non_us_test_features.geojson')) as testfile2:
        features2 = json.load(testfile2)
        testfile2.close()

    filtered2 = filter_features(features2, boundary_features)
    print filtered2
    print len(filtered2.get('passed').get('features'))
    print len(boundary_features)

if(__name__ == "__main__"):
    main()