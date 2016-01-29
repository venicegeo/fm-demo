# ALERTER DEMO

This is a django application which allows the user to connect to a kafka server and ingest data. If the data is a valid geojson feature it can be displayed on a map.

## Requirements

 - Python > 2.7
 
Python Dependencies (installable via pip)
    - django
    - kafka-python 
    
Additionally to Receive Kakfa alerts you need the kafka-devbox
https://github.com/venicegeo/kafka-devbox
    
## Setup 

From the alerter_demo folder run 

```
python initialize.py
```

This will delete any existing sqlite database, and reset any previous data migrations.

Subsequent runs can be started using:

```
python manage.py runserver 0.0.0.0:8000
```

Which will run a development webserver on port 80.

## Use

The alert register can be accessed at:
```
http://127.0.0.1:8000/alerts
```

A geojson of recieved alerts can be viewed at:
```
http://127.0.0.1:8000/alerts/geojson?topic=<topic_name>
```

A map can be used to view the data at:
```
http://127.0.0.1:8000/alerts/map?topic=<topic_name>
```

## Bugs
 - None known.
