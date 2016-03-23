import os
from importlib import import_module


def filter_features(features):
    """

    Args:
        features: A geojson Feature Collection

    Returns:
         Geojson Feature Collection that passed any filters in the in filter package
         If no features passed None is returned
    """

    from  django.core.exceptions import ObjectDoesNotExist
    from ..models import Filter
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
                        filter_entry = Filter.objects.get(filter_name=file)
                    except ObjectDoesNotExist:
                        print "Filter does not have associated model object"
                        continue

                    if filter_entry.filter_active == True:
                        try:
                            module_name = 'fulcrum_importer.filters.' + str(file.rstrip('.py'))
                            mod = import_module(module_name)
                            print "Running: {}".format(file)
                            filtered_results = mod.filter_features(filtered_features)

                        except ImportError:
                            print "Could not filter features - ImportError"
                        except TypeError:
                            print "Could not filter features - TypeError"

                        except Exception as e:
                            "Unknow error occured, could not filter features"
                            print repr(e)

                        if filtered_results:
                            if filtered_results.get('failed').get('features'):
                                print "{} features failed the filter".format(len(filtered_results.get('failed').get('features')))
                            if filtered_results.get('passed').get('features'):
                                print "{} features passed the filter".format(len(filtered_results.get('passed').get('features')))
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
