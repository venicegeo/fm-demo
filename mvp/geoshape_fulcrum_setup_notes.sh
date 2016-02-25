#!/bin/bash

#install fulcrum_importer
#add to /var/lib/geonode/rogue_geonode/geoshape/settings.py: 
cd ~
yum install unzip -y
wget https://github.com/venicegeo/fm-demo/archive/master.zip
unzip master.zip
mv -f fm-demo-master/alerter_demo_geoshape/fulcrum_importer /var/lib/geonode/lib/python2.7/site-packages/
chown geoshape:geoservice -R /var/lib/geonode/lib/python2.7/site-packages/fulcrum_importer

/var/lib/geonode/bin/pip install fulcrum
grep -qF "INSTALLED_APPS += ('fulcrum_importer',)" /var/lib/geonode/rogue_geonode/geoshape/settings.py || echo "INSTALLED_APPS += ('fulcrum_importer',)" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py

grep -q '^CELERY_ACCEPT_CONTENT' /var/lib/geonode/rogue_geonode/geoshape/settings.py && sed -i "s/^CELERY_ACCEPT_CONTENT.*/CELERY_ACCEPT_CONTENT=['json']/" /var/lib/geonode/rogue_geonode/geoshape/settings.py || echo "CELERY_ACCEPT_CONTENT=['json']" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py
grep -q '^CELERY_TASK_SERIALIZER' /var/lib/geonode/rogue_geonode/geoshape/settings.py && sed -i "s/^CELERY_TASK_SERIALIZER.*/CELERY_TASK_SERIALIZER='json'/" /var/lib/geonode/rogue_geonode/geoshape/settings.py || echo "CELERY_TASK_SERIALIZER='json'" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py
grep -q '^CELERY_RESULT_SERIALIZER' /var/lib/geonode/rogue_geonode/geoshape/settings.py && sed -i "s/^CELERY_RESULT_SERIALIZER.*/CELERY_RESULT_SERIALIZER='json'/" /var/lib/geonode/rogue_geonode/geoshape/settings.py || echo "CELERY_RESULT_SERIALIZER='json'" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py
grep -q '^CELERY_SEND_EVENTS' /var/lib/geonode/rogue_geonode/geoshape/settings.py && sed -i "s/^CELERY_SEND_EVENTS.*/CELERY_SEND_EVENTS=True/" /var/lib/geonode/rogue_geonode/geoshape/settings.py || echo "CELERY_SEND_EVENTS=True" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py
grep -q '^CELERYBEAT_USER' /var/lib/geonode/rogue_geonode/geoshape/settings.py && sed -i "s/^CELERYBEAT_USER.*/CELERYBEAT_USER='geoshape'/" /var/lib/geonode/rogue_geonode/geoshape/settings.py || echo "CELERYBEAT_USER='geoshape'" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py
grep -q '^CELERYBEAT_GROUP' /var/lib/geonode/rogue_geonode/geoshape/settings.py && sed -i "s/^CELERYBEAT_GROUP.*/CELERYBEAT_GROUP='geoservice'/" /var/lib/geonode/rogue_geonode/geoshape/settings.py || echo "CELERYBEAT_GROUP='geoservice'" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py
grep -q '^CELERYBEAT_SCHEDULER' /var/lib/geonode/rogue_geonode/geoshape/settings.py && sed -i "s/^CELERYBEAT_SCHEDULER.*/CELERYBEAT_SCHEDULER='djcelery\.schedulers\.DatabaseScheduler'/" /var/lib/geonode/rogue_geonode/geoshape/settings.py || echo "CELERYBEAT_SCHEDULER='djcelery.schedulers.DatabaseScheduler'" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py
grep -q '^CELERY_TIMEZONE' /var/lib/geonode/rogue_geonode/geoshape/settings.py && sed -i "s/^CELERY_TIMEZONE.*/CELERY_TIMEZONE='UTC'/" /var/lib/geonode/rogue_geonode/geoshape/settings.py || echo "CELERY_TIMEZONE='UTC'" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py
grep -q "from datetime import timedelta" /var/lib/geonode/rogue_geonode/geoshape/settings.py || echo "from datetime import timedelta" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py
grep -q "^CELERYBEAT_SCHEDULE =" /var/lib/geonode/rogue_geonode/geoshape/settings.py ||
printf "CELERYBEAT_SCHEDULE = {\n\
    'Update_layers_30_secs': {\n\
        'task': 'fulcrum_importer.tasks.task_update_layers',\n\
        'schedule': timedelta(seconds=30),\n\
        'args': None\n\
    },\n}" >> /var/lib/geonode/rogue_geonode/geoshape/settings.py

#add to /var/lib/geonode/rogue_geonode/geoshape/local_settings.py:

grep -q '^FULCRUM_UPLOAD' /var/lib/geonode/rogue_geonode/geoshape/local_settings.py && sed -i "s/^FULCRUM_UPLOAD.*/FULCRUM_UPLOAD='/var/lib/geonode/fulcrum_data'/" /var/lib/geonode/rogue_geonode/geoshape/local_settings.py || echo "FULCRUM_UPLOAD='/var/lib/geonode/fulcrum_data'" >> /var/lib/geonode/rogue_geonode/geoshape/local_settings.py
grep -q '^FULCRUM_API_KEY' /var/lib/geonode/rogue_geonode/geoshape/local_settings.py || echo "FULCRUM_API_KEY=''" >> /var/lib/geonode/rogue_geonode/geoshape/local_settings.py
grep -q '^DATA_FILTERS' /var/lib/geonode/rogue_geonode/geoshape/local_settings.py || echo "DATA_FILTERS=''" >> /var/lib/geonode/rogue_geonode/geoshape/local_settings.py

#add to /var/lib/geonode/rogue_geonode/geoshape/urls.py:
grep -qF 'from fulcrum_importer.urls import urlpatterns as fulcrum_importer_urls' /var/lib/geonode/rogue_geonode/geoshape/urls.py || 
printf "from fulcrum_importer.urls import urlpatterns as fulcrum_importer_urls\nurlpatterns += fulcrum_importer_urls" >> /var/lib/geonode/rogue_geonode/geoshape/urls.py

#add to /var/lib/geonode/rogue_geonode/geoshape/celery_app.py:
grep -qF 'from django.conf import settings' /var/lib/geonode/rogue_geonode/geoshape/celery_app.py || echo "from django.conf import settings" >> /var/lib/geonode/rogue_geonode/geoshape/celery_app.py
grep -qF 'app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)' /var/lib/geonode/rogue_geonode/geoshape/celery_app.py || echo "app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)" >> /var/lib/geonode/rogue_geonode/geoshape/celery_app.py

#add to /etc/supervisord.conf:
grep -qF 'programs=uwsgi,celery-worker1,celery-worker2,celery-worker3,celery-worker4,celery-worker5' /etc/supervisord.conf && sed -i "s/^programs.*/programs=uwsgi,celery-worker1,celery-worker2,celery-worker3,celery-worker4,celery-worker5,celery-beat/" /etc/supervisord.conf
grep -qF '[program:celery-beat]' /etc/supervisord.conf ||
printf "[program:celery-beat]\n\
command =   /var/lib/geonode/bin/celery beat\n\
            --app=geoshape.celery_app\n\
            --uid geoshape\n\
            --loglevel=info\n\
            --workdir=/var/lib/geonode/rogue_geonode\n\
stdout_logfile=/var/log/celery/celery-beat-stdout.log\n\
stderr_logfile=/var/log/celery/celery-beat-stderr.log\n\
autostart=true\n\
autorestart=true\n\
startsecs=10\n\
stopwaitsecs=600" >> /etc/supervisord.conf


# grep -q '^option' file && sed -i 's/^option.*/option=value/' file || echo 'option=value' >> file









#add to /var/lib/geonode/rogue_geonode/geoshape/settings.py: 
INSTALLED_APPS += ('fulcrum_importer') 

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_SEND_EVENTS = True
CELERYBEAT_USER="geoshape"
CELERYBEAT_GROUP="geoservice"
CELERYBEAT_SCHEDULER='djcelery.schedulers.DatabaseScheduler'

from datetime import timedelta
CELERYBEAT_SCHEDULE = {
    'Update_layers_30_secs': {
        'task': 'fulcrum_importer.tasks.task_update_layers',
        'schedule': timedelta(seconds=30),
        'args': None
    },
}

#add to /var/lib/geonode/rogue_geonode/geoshape/local_settings.py:

FULCRUM_UPLOAD = '/var/lib/geonode/fulcrum_data'

## put API key here 
FULCRUM_API_KEY = ''

## put data filters here
DATA_FILTERS = ['']

#add to /var/lib/geonode/rogue_geonode/geoshape/urls.py:

from fulcrum_importer.urls import urlpatterns as fulcrum_importer_urls
urlpatterns += fulcrum_importer_urls

#add to /var/lib/geonode/rogue_geonode/geoshape/celery_app.py:
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

