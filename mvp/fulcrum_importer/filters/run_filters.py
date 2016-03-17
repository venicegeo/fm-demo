import os
from importlib import import_module

def filter(features):
    workspace = os.path.dirname(os.path.abspath( __file__ ))
    files = os.listdir(workspace)
    filtered_features = features

    if filtered_features.get('features'):
        filtered_feature_count = len(filtered_features.get('features'))
        for file in files:
            if file.endswith('.py'):
                if file != 'run_filters.py' and file != '__init__.py':
                    try:
                        mod = import_module(file.rstrip('.py'))
                        filtered_results = mod.filter(filtered_features)
                    except (ImportError, TypeError):
                        pass
                    if filtered_results.get('failed').get('features'):
                        print("Some features failed the {} filter.".format(file.rstrip('.py')))
                    if filtered_results.get('passed').get('features'):
                        filtered_features = filtered_results.get('passed')
                        filtered_feature_count = len(filtered_results.get('passed').get('features'))
                    else:
                        filtered_features = None
                        filtered_feature_count = 0
                        return filtered_features, filtered_feature_count
    else:
        filtered_features = None
        filtered_feature_count = 0

    return filtered_features, filtered_feature_count

def main():
    import json
    with open(os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'us_test_features.geojson')) as testfile:
        features = json.load(testfile)
        testfile.close()

    filtered, count = filter(features)
    print filtered
    if filtered:
        print len(filtered.get('features'))

    with open(os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'non_us_test_features.geojson')) as testfile2:
        features2 = json.load(testfile2)
        testfile2.close()

    filtered2, count = filter(features2)
    print filtered2
    if filtered2:
        print len(filtered2.get('features'))

if(__name__ == "__main__"):
    main()