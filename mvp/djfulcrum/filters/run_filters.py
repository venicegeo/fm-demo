from __future__ import absolute_import

import os
from importlib import import_module
from django.core.cache import cache


def filter_features(features, filter_name=None, notify_filter=False):
    """

    Args:
        features: A geojson Feature Collection
        filter_name: The name of a filter to use if None all active filters are used (default:None)
        notify_filter: Used to notify the model when filtering is complete for use with filter_previous..
    Returns:
         Geojson Feature Collection that passed any filters in the in filter package
         If no features passed None is returned
    """

    from ..models import Filter
    from ..djfulcrum import delete_feature
    workspace = os.path.dirname(os.path.abspath( __file__ ))
    files = os.listdir(workspace)

    filtered_features = features

    if filtered_features.get('features'):
        filtered_feature_count = len(filtered_features.get('features'))
        filtered_results = None
        if filter_name:
            filter_entries = Filter.objects.filter(filter_name=filter_name)
        else:
            filter_entries = Filter.objects.all()
        if filter_entries:
            un_needed =[]
            for entry in filter_entries:
                if entry.filter_name in files:
                    if entry.filter_active:
                        try:
                            module_name = 'djfulcrum.filters.' + str(entry.filter_name.rstrip('.py'))
                            mod = import_module(module_name)
                            print "Running: {}".format(entry.filter_name)
                            filtered_results = mod.filter_features(filtered_features)
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
                                    delete_feature(feature.get('properties').get('fulcrum_id'))
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
                    un_needed.append(entry)
                if notify_filter:
                    entry.filter_previous_status = True
                    entry.save()
            if un_needed:
                for filter_entry in un_needed:
                    print "Deleting un-needed filter entry: {}".format(filter_entry.filter_name)
                    filter_entry.delete()

    else:
        filtered_features = None
        filtered_feature_count = 0
    print "Finished filtering"
    return filtered_features, filtered_feature_count


def check_filters():
    """
    Args: None
    Returns: None
    Finds '.py' files used for filtering and adds to db model for use in admin console.
    Sets cache value so function will not running fully every time it is called by tasks.py
    """
    from ..models import Filter
    workspace = os.path.dirname(os.path.abspath(__file__))
    files = os.listdir(workspace)
    if files:
        LOCK_EXPIRE = 10
        lock_id = 'list-filters-success'
        if cache.get(lock_id):
            return
        for filter_file in files:
                if filter_file.endswith('.py'):
                    if filter_file != 'run_filters.py' and filter_file != '__init__.py':
                        try:
                            filter_name, created = Filter.objects.get_or_create(filter_name=filter_file)
                            if created:
                                print "Created model object for {}".format(filter_file)
                        except Exception as e:
                            print repr(e)
                            continue
        cache.set(lock_id, True, LOCK_EXPIRE)
    return