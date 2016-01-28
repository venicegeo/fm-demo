from django.shortcuts import render
from piazza_consumer import consumer
from piazza_consumer.models import Listener, Key, Message, Asset
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
                return render(request, 'piazza_consumer/register.html', {'created': created_listener,'key':key})
            else:
                return HttpResponse("That listener already exists.",status=400)
    else:
        print "GET REQUEST"
        form = ListenerForm()
        keys = Key.objects.all().order_by('listener')
        return render(request, 'piazza_consumer/register.html', {'form': form,'keys':keys})


def messages(request):
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
                messages = Message.objects.filter(key=key)
            except ObjectDoesNotExist:
                return HttpResponse
            for alerts_msg in messages:
                text += str(alerts_msg.alert_date) + " " + alerts_msg.message + "<br>"
            return HttpResponse(text)
        else:
            text = ""
            messages = Message.objects.all().order_by('alert_date')
            for message in messages:
                text += str(message.alert_date) + " " + message.message + "<br>"
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
            return render(request, 'piazza_consumer/map.html', {'geojson_request_url':'/messages/geojson?topic='+str(request.GET['topic'])})
        else:
            return render(request, 'piazza_consumer/map.html', {'geojson_request_url':''})

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
            messages = Message.objects.filter(key=key)
        except ObjectDoesNotExist:
            return HttpResponse("No piazza_consumer exist",status=400)
        for feature in messages:
            json_feature = json.loads(feature.message_body)
            json_feature["properties"]["time"] = int(time.mktime(feature.message_date.timetuple()) * 1000)
            json_feature["properties"]["date"] = str(feature.message_date)
            features += [json_feature]

        feature_collection = {"type":"FeatureCollection","features": features}
        return json.dumps(feature_collection)
