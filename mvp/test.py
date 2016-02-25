def upload(feature_data, user, password, database, table):
    import json
    import subprocess
    import os.path

    for property in feature_data.get('properties'):
        if type(feature_data.get('properties').get(property)) == list:
            print "Changing {} to {}.".format(feature_data['properties'][property], ','.join(feature_data['properties'][property]))
            feature_data['properties'][property] = ','.join(feature_data['properties'][property])

    print str(feature_data)

    temp_file = os.path.abspath('./temp.json')
    temp_file = '/'.join(temp_file.split('\\'))
    with open(temp_file, 'w') as open_file:
        open_file.write(json.dumps(feature_data))
    out = ""
    conn_string = "host=localhost dbname={} user={} password={}".format(database, user, password)
    execute = ['ogr2ogr',
               '-f', 'PostgreSQL',
               '-append',
               'PG:"{}"'.format(conn_string),
               temp_file,
               '-nln', table
               ]
    print ' '.join(execute)
    # try:
    #     out = subprocess.call(' '.join(execute), shell=True)
    #     print "Uploaded the feature {} to postgis.".format(feature_data.get('properties').get('city'))
    # except subprocess.CalledProcessError:
    #     print "Failed to call:\n" + ' '.join(execute)
    #     print out

def importer(feature_data):
    import json
    import requests
    import os.path

    temp_file = os.path.abspath('./temp.json')
    temp_file = '/'.join(temp_file.split('\\'))
    with open(temp_file, 'w') as open_file:
        open_file.write(json.dumps(feature_data))

    headers = {'Content-Type': 'application/json'}
    auth = ("admin", "geoshape")
    url = "https://geoshape.dev/geoserver/rest/imports"

    data = {"import": {"targetWorkspace": {"workspace": {"name": "geonode"}}, "targetStore": {},
                       "dataStore": {"name": "od3_repo"}, "data": {"type": "file",
                                                                   "file": temp_file}},
            "task": {"updateMode": "APPEND"}}

    json_data = json.dumps(data)
    print json_data

    resp = requests.post(url, data=json_data, headers=headers, auth=auth, verify=False)
    print str(resp.status_code) + ":" + resp.text
    # json_obj = json.loads(resp.text)
    # url = json_obj['import']['href']

    # requests.post(url, auth=auth)


def main():
    feature = {
            "type": "Feature",
            "properties": {
                "fulcrum_id": "1c3659ef-1040-49c2-9750-65bb84b66dd0",
                "created_at": "2016-01-14 02:05:33 UTC",
                "updated_at": "2016-01-14 02:05:33 UTC",
                "created_by": "knaquin@radiantblue.com",
                "updated_by": "knaquin@radiantblue.com",
                "system_created_at": "2016-01-14 02:05:33 UTC",
                "system_updated_at": "2016-01-14 02:05:33 UTC",
                "version": 1,
                "change_type": "create",
                "status": None,
                "project": None,
                "assigned_to": None,
                "latitude": -12.0561399459839,
                "longitude": -77.0268020629883,
                "changeset_id": "3fcd7bb3-9e6f-49d7-8f33-b26a914044a3",
                "name": "Polo",
                "store_number": "38603-95353",
                "phone_number": None,
                "address_1": "Av. El Polo 709, Frente a C.C. El Polo",
                "address_2": "Surco",
                "address_3": None,
                "city": "Lima",
                "country": "PE",
                "postal_code": "33",
                "photos": ['photo1', 'photo2'],
                "photos_caption": None,
                "photos_url": ['/url1', '/url2'],
                "gps_altitude": None,
                "gps_horizontal_accuracy": None,
                "gps_vertical_accuracy": None,
                "gps_speed": None,
                "gps_course": None
            },
            "geometry": {
                "type": "Point",
                "coordinates": [-77.0268020629883, -12.0561399459839]
            }
    }

    upload(feature, 'geoshape', 'gE8rCp5cSmUKM8kX', 'fulcrum', 'starbucks')



if __name__ == "__main__":
    main()
