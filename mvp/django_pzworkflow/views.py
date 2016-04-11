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
from .forms import UploadFulcrumData
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core import exceptions
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


def pzworkflow(request):
    import types
    from .fetch_workflow import PzWorkflow
    if request.method == 'POST':
        json_data = request.body
        print "Data passed in: " + json_data
        pz = PzWorkflow("https://pz-workflow.stage.geointservices.io")
        print "Pz health check returned: " + str(pz.status())
        if pz.status() == 200:
            response = pz.request(json_data)
            if response:
                user_request = json.loads(json_data)
                if(user_request.get('action') == 'get'):
                    return HttpResponse(json.dumps(response), content_type="application/json")
                elif(user_request.get('action') == 'post'):
                    if isinstance(response, types.DictType):
                        return HttpResponse(json.dumps(response), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps(response.json()), content_type="application/json")
                elif(user_request.get('action') == 'get_all'):
                    return HttpResponse(json.dumps(response.json()), content_type="application/json")
                elif(user_request.get('action') == 'delete'):
                    return HttpResponse(json.dumps(response.json()), content_type="application/json")
                else:
                    return HttpResponse("What on earth happened", status=400)
            else:
                return HttpResponse("Error with your request.", status=400)
        else:
            return HttpResponse("Pz-Workflow does not appear to be running", status=400)


def pz_models(request):
    from .mapping import get_pz_events, get_pz_triggers, get_pz_features
    if request.method == 'GET':
        models = {'events': get_pz_events(), 'triggers': get_pz_triggers(), 'features': get_pz_features()}
        return HttpResponse(json.dumps(models), content_type="application/json")

    if request.method == 'POST':
        from .models import PzEvents, PzTriggers, PzFeatures
        json_data = json.loads(request.body)
        if 'post' in json_data:
            json_data = json_data.get('post')
            if json_data.get('events'):
                events_dict = json_data.get('events')
                for event_id in events_dict:
                    event_info = events_dict.get(event_id)
                    lat, lng, event_data = None, None, None
                    if 'coordinates' in event_info:
                        lat = event_info.get('coordinates')[1]
                        lng = event_info.get('coordinates')[0]
                    if 'event_data' in event_info:
                        event_data = event_info.get('event_data')
                    model, created = PzEvents.objects.get_or_create(event_id=event_id,
                                                                    event_data=json.dumps(event_data), event_lat=lat, event_lng=lng)

            if json_data.get('triggers'):
                triggers_dict = json_data.get('triggers')
                for trigger_id in triggers_dict:
                    trigger_info = triggers_dict.get(trigger_id)
                    trigger_data = None
                    if 'trigger_data' in trigger_info:
                        trigger_data = trigger_info.get('trigger_data')
                    model, created = PzTriggers.objects.get_or_create(trigger_id=trigger_id, trigger_data=json.dumps(trigger_data))

            if json_data.get('features'):
                features_array = json_data.get('features')
                for feature in features_array:
                    model, created = PzFeatures.objects.get_or_create(feature=json.dumps(feature))


            models = {'events': get_pz_events(), 'triggers': get_pz_triggers(), 'features': get_pz_features()}
            return HttpResponse(json.dumps(models), content_type="application/json")

        if 'delete' in json_data:
            json_data = json_data.get('delete')
            if json_data.get('events'):
                events_dict = json_data.get('events')
                for event_id in events_dict:
                    try:
                        model = PzEvents.objects.get(event_id=event_id)
                        model.delete()
                    except exceptions.ObjectDoesNotExist:
                        print "Not found"

            if json_data.get('triggers'):
                triggers_dict = json_data.get('triggers')
                for trigger_id in triggers_dict:
                    try:
                        model = PzTriggers.objects.get(trigger_id=trigger_id)
                        model.delete()
                    except exceptions.ObjectDoesNotExist:
                        print "Not found"

            if json_data.get('features'):
                features_array = json_data.get('features')
                for feature in features_array:
                    try:
                        model = PzFeatures.objects.get(feature=json.dumps(feature))
                        model.delete()
                    except exceptions.ObjectDoesNotExist:
                        print "Not found"

            models = {'events': get_pz_events(), 'triggers': get_pz_triggers(), 'features': get_pz_features()}
            return HttpResponse(json.dumps(models), content_type="application/json")

    return HttpResponse("Error with your request.", status=400)






