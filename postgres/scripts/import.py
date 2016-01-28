#!/usr/bin/env python

import json
import requests

headers= {'Content-Type': 'application/json'}
auth = ("admin", "admin")
url = "http://localhost:8080/geoserver/rest/imports"

with open("import.json","rb") as f:
  resp = requests.post(url, data=f, headers=headers, auth=auth)
json_obj = json.loads(resp.text)
url = json_obj['import']['href']

requests.post(url, auth=auth)


