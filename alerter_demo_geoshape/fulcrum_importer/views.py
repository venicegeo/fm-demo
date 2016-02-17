# Copyright 2016, RadiantBlue Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.shortcuts import render
from .models import Asset
from .forms import ListenerForm, UploadFulcrumData
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import json
import time
import os

def index(request):
    return viewer(request)

def geojson(request):
    from .mapping import get_geojson
    if request.method=='GET':
        if 'layer' not in request.GET:
            return HttpResponse("No layer exists, or a layer was not specified.",status=400)
        geojson = {}
        for layer in request.GET.getlist('layer'):
            if get_geojson(layer):
                geojson[layer] = json.loads(get_geojson(layer))
    if not geojson:
        return HttpResponse("No layer exists, or a layer was not specified.",status=400)
    return HttpResponse(json.dumps(geojson), content_type="application/json")


def upload(request):
    from .fulcrum_importer import process_fulcrum_data
    from .mapping import get_geojson

    if request.method == 'POST':
        form = UploadFulcrumData(request.POST, request.FILES)
        print request.FILES
        geojson = {}
        if form.is_valid():
            layers = process_fulcrum_data(request.FILES['file'])
            for layer in layers:
                if get_geojson(layer):
                    geojson[layer] = json.loads(get_geojson(layer))
            return HttpResponse(json.dumps(geojson), content_type="application/json")
        else:
            print "FORM NOT VALID."
    else:
        form = UploadFulcrumData()
    return render(request, 'fulcrum_importer/upload.html', {'form': form})


def viewer(request):
    from .mapping import get_geojson
    if request.method=='GET':
        if 'layer' not in request.GET:
            return render(request, 'fulcrum_importer/map.html', {'geojson_request_url':''})
        geojson = {}
        layers = []
        for layer in request.GET.getlist('layer'):
            if get_geojson(layer):
                layers += ['layer=' + layer]
        if geojson:
            return render(request, 'fulcrum_importer/map.html', {'geojson_request_url':'/fulcrum_importer/geojson?{}'+'&'.join(layers)})
        else:
            return render(request, 'fulcrum_importer/map.html', {'geojson_request_url':''})


def layers(request):
    from .mapping import get_layer_names
    return HttpResponse(json.dumps(get_layer_names()), content_type="application/json")

