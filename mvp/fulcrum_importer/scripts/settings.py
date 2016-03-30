SSL_VERIFY = False

FULCRUM_UPLOAD = '/var/lib/geonode/fulcrum_data'

DATABASES = {}

DATABASES['default'] = {}

DATABASES['fulcrum'] = {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'fulcrum_data',
        'USER': 'admin',
        'PASSWORD': 'geoserver',
        'HOST': 'localhost',
        'PORT': '5432', #Notice: string
    }


S3_CREDENTIALS = [{'s3_bucket': ['xxxxx'],
                  's3_key': 'xxxxx',
                  's3_secret': 'xxxxx',
                  's3_gpg': 'xxxxx'},
                  {'s3_bucket': ['xxxxx'],
                  's3_key': 'xxxxx',
                  's3_secret': 'xxxxx',
                  's3_gpg': 'xxxxx'}]

FULCRUM_API_KEYS=['xxxx']

SITEURL = 'https://geoshape.dev/'

GEOSERVER_URL = SITEURL + 'geoserver/'

OGC_SERVER = {
    'default' : {
        'BACKEND' : 'geonode.geoserver',
        'LOCATION' : GEOSERVER_URL,
        'PUBLIC_LOCATION' : GEOSERVER_URL,
        'USER' : 'admin',
        'PASSWORD' : 'geoserver',
        'MAPFISH_PRINT_ENABLED' : True,
        'PRINT_NG_ENABLED' : True,
        'GEONODE_SECURITY_ENABLED' : True,
        'GEOGIG_ENABLED' : True,
        'WMST_ENABLED' : False,
        'DATASTORE': 'geoshape_imports',
        'GEOGIG_DATASTORE_DIR':'/var/lib/geoserver_data/geogig',
    }
}

INSTALLED_APPS = ()
INSTALLED_APPS += ('fulcrum_importer',)

CELERY_ACCEPT_CONTENT=['json']

CELERY_TASK_SERIALIZER='json'

CELERY_RESULT_SERIALIZER='json'

CELERY_SEND_EVENTS=True

CELERYBEAT_USER='geoshape'

CELERYBEAT_GROUP='geoservice'

CELERYBEAT_SCHEDULER='djcelery.schedulers.DatabaseScheduler'

from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'Update_layers_30_secs': {
        'task': 'fulcrum_importer.tasks.task_update_layers',
        'schedule': timedelta(seconds=30),
        'args': None
    },
   'pull_s3_data_60_secs': {
        'task': 'fulcrum_importer.tasks.pull_s3_data',
        'schedule': timedelta(seconds=60),
        'args': None
    },

}

USE_TZ = False

TIME_ZONE = None

CACHES = {
     'default': {
         'BACKEND':
         'django.core.cache.backends.memcached.MemcachedCache',
         'LOCATION': '127.0.0.1:11211',
     }
}

