import os
from importlib import import_module
import copy


def filter(features):
    """

    Args:
        features: A geojson Feature Collection

    Returns:
         Geojson Feature Collection that passed any filters in the in filter package
         If no features passed None is returned
    """

    import json
    workspace = os.path.dirname(os.path.abspath( __file__ ))
    files = os.listdir(workspace)

    filtered_features = features

    if filtered_features.get('features'):
        filtered_feature_count = len(filtered_features.get('features'))
        filtered_results = None
        for file in files:
            if file.endswith('.py'):
                if file != 'run_filters.py' and file != '__init__.py':
                    try:
                        module_name = 'fulcrum_importer.filters.' + str(file.rstrip('.py'))
                        mod = import_module(module_name)
                        print "Running: {}".format(file)
                        filtered_results = mod.filter(filtered_features)

                    except ImportError:
                        print "Could not filter features - ImportError"
                    except TypeError:
                        print "Could not filter features - TypeError"

                    except Exception as e:
                        "Unknow error occured, could not filter features"
                        print repr(e)

                    if filtered_results:
                        if filtered_results.get('failed').get('features'):
                            print("Some features failed the {}.".format(file.rstrip('.py')))
                        if filtered_results.get('passed').get('features'):
                            print ("Some features passed the filter")
                            filtered_features = filtered_results.get('passed')
                            filtered_feature_count = len(filtered_results.get('passed').get('features'))
                        else:
                            filtered_features = None
                            filtered_feature_count = 0
                            return filtered_features, filtered_feature_count
                    else:
                        print "Failure to get filtered results"
    else:
        filtered_features = None
        filtered_feature_count = 0
    print "Finished filtering"
    return filtered_features, filtered_feature_count