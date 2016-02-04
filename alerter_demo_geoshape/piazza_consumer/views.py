from django.shortcuts import render
from piazza_consumer.models import Asset
from .forms import ListenerForm, UploadFulcrumData
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import json
import time
import os

def index(request):
    pass

def geojson(request):
    from mapping import get_geojson
    if request.method=='GET':
        if 'layer' not in request.GET:
            return None
        geojson = {}
        for layer in request.GET.getlist('layer'):
            geojson[layer] = json.loads(get_geojson(layer))
    if not geojson:
        return HttpResponse("A topic must be specific as a GET parameter.",status=400)
    return HttpResponse(json.dumps(geojson), content_type="application/json")


def upload(request):
    from fulcrum import process_fulcrum_data
    from mapping import get_geojson

    if request.method == 'POST':
        form = UploadFulcrumData(request.POST, request.FILES)
        print request.FILES
        geojson = {}
        if form.is_valid():
            layers = process_fulcrum_data(request.FILES['file'])
            for layer in layers:
                geojson[layer] = json.loads(get_geojson(layer))
            return HttpResponse(json.dumps(geojson), content_type="application/json")
        else:
            print "FORM NOT VALID."
    else:
        form = UploadFulcrumData()
    return render(request, 'piazza_consumer/upload.html', {'form': form})


def map(request):
    from mapping import get_geojson
    if request.method=='GET':
        if 'layer' not in request.GET:
            return render(request, 'piazza_consumer/map.html', {'geojson_request_url':''})
        geojson = {}
        layers = []
        for layer in request.GET.getlist('layer'):
            geojson[layer] = json.loads(get_geojson(layer))
            layers += ['layer=' + layer]
        if geojson:
            return render(request, 'piazza_consumer/map.html', {'geojson_request_url':'/messages/geojson?{}'+str(request.GET['topic'])})
        else:
            return render(request, 'piazza_consumer/map.html', {'geojson_request_url':''})



