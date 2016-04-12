from __future__ import absolute_import

import os
from importlib import import_module
from django.core.cache import cache


def filter_features(features, filter_name=None, run_once=False):
    """

    Args:
        features: A geojson Feature Collection
        filter_name: The name of a filter to use if None all active filters are used (default:None)
        run_once: Run the filter one time without being active.
    Returns:
         Geojson Feature Collection that passed any filters in the in filter package
         If no features passed None is returned
    """

    from ..models import Filter
    from ..djfulcrum import delete_feature
    workspace = os.path.dirname(os.path.abspath(__file__))
    files = os.listdir(workspace)

    if features.get('features'):
        filtered_feature_count = len(features.get('features'))
        filtered_results = None
        if filter_name:
            filter_models = Filter.objects.filter(filter_name__iexact=filter_name)
        else:
            filter_models = Filter.objects.all()
        if filter_models:
            un_needed = []
            for filter_model in filter_models:
                if filter_model.filter_name in files:
                    if filter_model.filter_active or run_once:
                        try:
                            module_name = 'djfulcrum.filters.' + str(filter_model.filter_name.rstrip('.py'))
                            mod = import_module(module_name)
                            print "Running: {}".format(filter_model.filter_name)
                            filtered_results = mod.filter_features(features)
                        except ImportError:
                            print "Could not filter features - ImportError"
                        except TypeError:
                            print "Could not filter features - TypeError"
                        except Exception as e:
                            "Unknown error occurred, could not filter features"
                            print repr(e)
                        if filtered_results:
                            if filtered_results.get('failed').get('features'):
                                for feature in filtered_results.get('failed').get('features'):
                                    if run_once:
                                        delete_feature(feature.get('properties').get('fulcrum_id'))
                                print "{} features failed the filter".format(
                                        len(filtered_results.get('failed').get('features')))
                            if filtered_results.get('passed').get('features'):
                                print "{} features passed the filter".format(
                                        len(filtered_results.get('passed').get('features')))
                                features = filtered_results.get('passed')
                                filtered_feature_count = len(filtered_results.get('passed').get('features'))
                            else:
                                features = None
                                filtered_feature_count = 0
                        else:
                            print "Failure to get filtered results"
                else:
                    un_needed.append(filter_model)
            if un_needed:
                for filter_model in un_needed:
                    print "Deleting un-needed filter entry: {}".format(filter_model.filter_name)
                    filter_model.delete()
    else:
        features = None
        filtered_feature_count = 0
    return features, filtered_feature_count


def check_filters(test=None):
    """
    Args:
        test: should be set to try if running tests.
    Returns: None
    Finds '.py' files used for filtering and adds to db model for use in admin console.
    Sets cache value so function will not running fully every time it is called by tasks.py
    """
    from ..models import Filter, get_defaults
    workspace = os.path.dirname(os.path.abspath(__file__))
    files = os.listdir(workspace)
    if files:
        lock_expire = 10
        lock_id = 'list-filters-success'
        if cache.get(lock_id):
            return
        for filter_file in files:
            if filter_file.endswith('.py'):
                if filter_file.lower() != 'run_filters.py' and filter_file.lower() != '__init__.py':
                    if test:
                        if not filter_file.startswith('test_'):
                            continue
                    else:
                        if filter_file.startswith('test_'):
                            continue
                    try:
                        filter_names = Filter.objects.filter(filter_name=filter_file)
                        if not filter_names:
                            Filter.objects.create(filter_name=filter_file)
                    except Exception as e:
                        print repr(e)
                        continue
        cache.set(lock_id, True, lock_expire)
    return
