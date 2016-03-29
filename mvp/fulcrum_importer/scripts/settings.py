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
