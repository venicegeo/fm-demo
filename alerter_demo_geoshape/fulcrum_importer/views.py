from django.shortcuts import render
from fulcrum_importer.models import Asset
from .forms import ListenerForm, UploadFulcrumData
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import json
import time
import os

def index(request):
    return viewer(request)

def geojson(request):
    from mapping import get_geojson
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
    from geoshape_fulcrum import process_fulcrum_data
    from mapping import get_geojson

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
    from mapping import get_geojson
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



