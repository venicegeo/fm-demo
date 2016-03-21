from types import *
import json
import copy
import re


def filter(input):
    """
    Args:
         input: A Geojson feature collection

    Returns:
        A json of two geojson feature collections: passed and failed
    """
    passed_failed = filter_number_features(input)
    return passed_failed


def filter_number_features(input_features):
    if type(input_features) is DictType:
        if input_features.get("features"):
            return iterate_geojson(input_features)
    #     else:
    #         return iterate_json(input_features)
    #
    # elif type(input_features) is ListType:
    #     return iterate_array(input_features)
    else:
        print "Returning none"
        print type(input_features)
        return None


def iterate_geojson(input_features):
    """
    Args:
         input: A Geojson feature collection

    Returns:
        A json of two geojson feature collections: passed and failed
    """
    passed = []
    failed = []
    for feature in input_features.get("features"):
        if not feature:
            continue
        if check_numbers(json.dumps(feature.get('properties'))):
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


# def iterate_json(input_features):
#     passed = []
#     failed = []
#     if check_numbers(input_features):
#         failed.append(input_features)
#     else:
#         passed.append(input_features)
#
#     return {'passed': passed, 'failed': failed}
#
#
# def iterate_array(input_features):
#     passed = []
#     failed = []
#     for feature in input_features:
#         if check_numbers(input_features[feature]):
#             failed.append(input_features[feature])
#         else:
#             passed.append(input_features[feature])
#     return {'passed': passed, 'failed': failed}


def check_numbers(attributes):
    """
    Args:
         attributes: Stringified properties of a geojson feature

    Returns:
        True if a US phone number is found in the string
        False if there is no US phone number found in the string
    """
    pattern = re.compile('([^0-9]+[(]?[2-9]\d{2}[)]?|^[(]?[2-9]\d{2}[)]?)[^a-zA-Z0-9][2-9]\d{2}(\s|-|[.])(\d{4}[^0-9]+|\d{4}$)')
    phone_number = pattern.search(attributes)
    if phone_number:
        area_code_pattern = re.compile('[2-9]\d{2}')
        area_code = int(area_code_pattern.search(phone_number.group()).group())
        area_codes = get_area_codes()
        if area_code in area_codes:
            return True
        else:
            return False
    else:
        return False


def get_area_codes():
    """
    Args:
        None

    Returns:
         An array of US phone area codes
    """

    area_codes = [
        205, 251, 256, 334, 938,  # Alabama
        907, 250,  # Alaska
        480, 520, 602, 623, 928,  # Arizona
        327, 479, 501, 870,  # Arkansas
        209, 213, 310, 323, 408, 415, 424, 442, 510, 530, 559, 562, 619, 626, 628, 650, 657, 661, 669, 707, 714, 747, 760, 805, 818, 831, 858, 909, 916, 925, 949, 951,  # California
        303, 719, 720, 970,  # Colorado
        203, 475, 860, 959,  # Connecticut
        302,  # Deleware
        202,  # District of Columbia
        239, 305, 321, 352, 386, 407, 561, 727, 754, 772, 786, 813, 850, 863, 904, 941, 954,  # Florida
        229, 404, 470, 478, 678, 706, 762, 770, 912,  # Georgia
        808,  # Hawaii
        208, 986,  # Idaho
        217, 224, 309, 312, 331, 447, 464, 618, 630, 708, 730, 773, 779, 815, 847, 872,  # Illinois
        219, 260, 317, 463, 574, 765, 812, 930,  # Indiana
        319, 515, 563, 641, 712,  # Iowa
        316, 620, 785, 913,  # Kansas
        270, 364, 502, 606, 859,  # Kentucky
        225, 318, 337, 504, 985,  # Louisiana
        207,  # Maine
        227, 240, 301, 410, 443, 667,  # Maryland
        339, 351, 413, 508, 617, 774, 781, 857, 978,  # Massachusetts
        231, 248, 269, 313, 517, 586, 616, 734, 810, 906, 947, 989,  # Michigan
        218, 320, 507, 612, 651, 763, 952,  # Minesota
        228, 601, 662, 769,  # Mississippi
        314, 417, 573, 636, 660, 816, 975,  # Missouri
        406,  # Montana
        308, 402, 531,  # Nebraska
        702, 725, 775,  # Nevada
        603,  # New Hampshire
        201, 551, 609, 732, 848, 856, 862, 908, 973,  # New Jersey
        505, 575,  # New Mexico
        212, 315, 332, 347, 516, 518, 585, 607, 631, 646, 680, 716, 718, 845, 914, 917, 929, 934,  # New York
        252, 336, 704, 743, 828, 910, 919, 980, 984,  # North Carolina
        701,  # North Dakota
        216, 220, 234, 283, 330, 380, 419, 440, 513, 567, 614, 740, 937,  # Ohio
        405, 539, 580, 918,  # Oklahoma
        458, 503, 541, 971,  # Oregon
        215, 267, 272, 412, 484, 570, 610, 717, 724, 814, 878,  # Pennsylvania
        401,  # Rhode Island
        803, 843, 854, 864,  # South Carolina
        605,  # South Dakota
        423, 615, 629, 731, 865, 901, 931,  # Tennessee
        210, 214, 254, 281, 325, 346, 361, 409, 430, 432, 469, 512, 682, 713, 737, 806, 817, 830, 832, 903, 915, 936, 940, 956, 972, 979,  # Texas
        385, 435, 801,  # Utah
        802,  # Vermont
        276, 434, 540, 571, 703, 757, 804,  # Virginia
        206, 253, 360, 425, 509, 564,  # Washington
        304, 681,  # West Virginia
        262, 274, 414, 534, 608, 715, 920,  # Wisconsin
        307  # Wyoming
    ]
    return area_codes
