from django.shortcuts import render
from alerts import consumer
from alerts.models import Listener, Key, Alert
from .forms import ListenerForm
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
import json
import time

def index(request):
    if request.method=='POST':
        print "POST REQUEST"
        topic = None
        key = None
        error = ""
        if 'listener_topic' in request.POST:
            listener_topic = request.POST['listener_topic']
        else:
            error += "A topic is required.<br>"
        if 'listener_key' in request.POST:
            listener_key = request.POST['listener_key']
        else:
            error += "A key is required.<br>"
        if error:
            return HttpResponse(error)
        else:
            key, created_listener = consumer.write_listener('consumer', listener_topic, listener_key)
            if created_listener:
                return render(request, 'register.html', {'created': created_listener,'key':key})
            else:
                return HttpResponse("That listener already exists.",status=400)
    else:
        print "GET REQUEST"
        form = ListenerForm()
        keys = Key.objects.all().order_by('listener')
        return render(request, 'register.html', {'form': form,'keys':keys})


def alerts(request):
    if request.method=='GET':
        if 'topic' in request.GET:
            print "Searching for {}".format(str(request.GET['topic']))
            try:
                listener = Listener.objects.get(listener_topic=request.GET['topic'])
            except ObjectDoesNotExist:
                return HttpResponse("The {} listener does not exist.".format(request.GET['topic']),status=400)
            try:
                key = Key.objects.get(listener=listener, listener_key='feature')
            except ObjectDoesNotExist:
                return HttpResponse("The {} listener is not listening for features.".format(request.GET['topic']),status=400)
            text = ""
            try:
                alert_msgs = Alert.objects.filter(key=key)
            except ObjectDoesNotExist:
                return HttpResponse
            for alerts_msg in alert_msgs:
                text += str(alerts_msg.alert_date) + " " + alerts_msg.alert_msg + "<br>"
            return HttpResponse(text)
        else:
            text = ""
            alert_msgs = Alert.objects.all().order_by('alert_date')
            for alerts_msg in alert_msgs:
                text += str(alerts_msg.alert_date) + " " + alerts_msg.alert_msg + "<br>"
            return HttpResponse(text)


def geojson(request):
    if request.method=='GET':
        if 'topic' not in request.GET:
            return HttpResponse("You must provide a new ")
    geojson = __get_geojson(request)
    if not geojson:
        return HttpResponse("A topic must be specific as a GET parameter.",status=400)
    return HttpResponse(geojson)

def map(request):
    if request.method=='GET':
        geojson = __get_geojson(request)
        if type(geojson) == 'HttpResponse':
            return geojson
        if geojson:
            return render(request, 'map.html', {'geojson_request_url':'/alerts/geojson?topic='+str(request.GET['topic'])})
        else:
            return render(request, 'map.html', {'geojson_request_url':''})

def __get_geojson(request):
        print "Searching for {}".format(str(request.GET['topic']))
        try:
            listener = Listener.objects.get(listener_topic=request.GET['topic'])
        except ObjectDoesNotExist:
            return HttpResponse("The {} listener does not exist.".format(request.GET['topic']),status=400)
        try:
            key = Key.objects.get(listener=listener, listener_key='feature')
        except ObjectDoesNotExist:
            return HttpResponse("The {} listener is not listening for features.".format(request.GET['topic']),status=400)
        features = []
        try:
            alert_msgs = Alert.objects.filter(key=key)
        except ObjectDoesNotExist:
            return HttpResponse("No alerts exist",status=400)
        for feature in alert_msgs:
            json_feature = json.loads(feature.alert_msg)
            json_feature["properties"]["time"] = int(time.mktime(feature.alert_date.timetuple()) * 1000)
            json_feature["properties"]["date"] = str(feature.alert_date)
            features += [json_feature]

        feature_collection = {"type":"FeatureCollection","features": features}
        return json.dumps(feature_collection)
