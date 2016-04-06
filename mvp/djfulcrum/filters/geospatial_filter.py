import os
from shapely.geometry import Point, MultiPolygon, Polygon, shape
from types import *
import json
import copy


def filter_features(input):
    """
    Args:
         input: A Geojson feature collection

    Returns:
        A json of two geojson feature collections: passed and failed
    """
    boundary_features = get_boundary_features()
    passed_failed = filter_spatial_features(input, boundary_features)
    return passed_failed

def filter_spatial_features(input_features, boundary_features):
    """
    Args:
         input:
            input_features: A Geojson feature collection
            boundary_features: An array of shapely polygons/multipolygons used to filter features

    Returns:
        A json of two geojson feature collections: passed and failed, or None if input is not geojson
    """
    if type(input_features) is DictType:
        if input_features.get("features"):
            return iterate_geojson(input_features, boundary_features)
    else:
        print "Returning none"
        print type(input_features)
        return None

def iterate_geojson(input_features, boundary_features):
    """
    Args:
         input_features: A Geojson feature collection
         boundary_features: An array of shapely Polygons/MultiPolygons used to filter features

    Returns:
        A json of two geojson feature collections: passed and failed
    """

    passed = []
    failed = []
    for feature in input_features.get("features"):
        if not feature or not feature.get('geometry'):
            continue

        coords = feature.get('geometry').get('coordinates')

        if coords:
            if check_geometry(coords, boundary_features):
                failed.append(feature)
            else:
                passed.append(feature)

    passed_features = copy.deepcopy(input_features)
    passed_features['features'] = passed
    failed_features = input_features
    failed_features['features'] = failed
    return {'passed': passed_features, 'failed': failed_features}


def check_geometry(coords, boundary_features):
    """
    Args:
        coords: Array of coordinates
        boundary_features: An array of shapely Polygons/MultiPolygons used to filter features

    Returns:
         True if coordinates lie within any boundary_features
         False if coordinate do not lie within any boundary_features
    """
    point = Point(coords[0], coords[1])
    for index, boundary in enumerate(boundary_features):
        if boundary_features[index].contains(point):
            return True
    return False

def get_boundary_features():
    """
    Args:
        None

    Returns:
         An array of shapely Polygons or MultiPolygons from the boundary_polygon file which should contain geojson files
    """
    polygons = []
    filepath = os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'boundary_polygons')
    files = os.listdir(filepath)
    for file in files:
        if file.endswith('.geojson'):
            with open(os.path.join(filepath, file)) as file_data:
                try:
                    data = json.load(file_data)
                    geometry = shape(data.get('geometry')).buffer(0.1)
                    if geometry.geom_type is 'MultiPolygon' or geometry.geom_type is 'Polygon':
                        polygons.append(geometry)
                    file_data.close()
                except ValueError:
                    print "Error getting polygon data"
                    file_data.close()
    return polygons
