# django-fulcrum

This is a django application which allows the user to connect to a Fulcrumapp.com and ingest data, including all media files.

## Requirements

GDAL
GEOS
Python 2.7 with the following packages.
 - celery
 - django-celery
 - fulcrum
 - python-memcached
 - boto3
 - Pillow<=2.9.0
 - django
 - gsconfig
 - requests
 - shapely
 - gdal

The install script for geoshape using the geoshape-vagrant VM will be handled automatically.
Note that GEOS and GDAL are needed with their python bindings, additionally shapely needs to have a compatibly version of GEOS.
Therefore if your platform has a package already created called something similar to, "python-shapely" or "python-gdal" this will probably be
the easiest route to success.

## Setup 

There are two different types of installation instructions.  A set of instructions for using the geoshape-vagrant vm (recommended) or integrating the app into your own project.

### geoshape-vagrant setup

Download the geoshape-vagrant repo.
```
https://github.com/ROGUE-JCTD/geoshape-vagrant
```

In an elevated session (sudo or "run as administrator),
change directories to the geoshape-vagrant repo, and install the vagrant hosts updater
```
vagrant plugin install vagrant-hostsupdater
```

Copy the vagrant files from fm-mvp/vagrant_files into your geoshape-vagrant folder.  Also ensure that your geoshape vagrant folder exists on a large disk since by default the scripts will create a disk with a 500 GB capacity (thin provisioned).  

Bring up the geoshape vm.
```
vagrant up
```

SSH into the VM and run the following commands
```
cd /tmp
wget https://raw.githubusercontent.com/venicegeo/fm-mvp/master/mvp/djfulcrum/scripts/geoshape_fulcrum_install.sh -O- | tr -d '\r' > /tmp/geoshape_fulcrum_install.sh
sudo bash /tmp/geoshape_fulcrum_install.sh
```

You can modify your fulcrum api key entry in /var/lib/geonode/rogue_geonode/geoshape/local_settings.py file (sudo required).
```
FULCRUM_API_KEYS = ["xxxxx"]
```
Additionally in local_settings an S3_CREDENTIALS dict structured like:

```
S3_CREDENTIALS = [{'s3_bucket': ["xxxxx"],
                   's3_key': "xxxxx",
                   's3_secret': "xxxxx",
                   's3_gpg': "xxxxx"},
                   {'s3_bucket': ["xxxxx"],
                   's3_key': "xxxxx",
                   's3_secret': "xxxxx",
                   's3_gpg': "xxxxx"}]
```

Alternatively you may enter this information in the admin console.  It is more secure in the local_settings file, but the server would need to be restarted, after information is added or removed.

To allow for geoshape tile truncation on addition of new data, make sure there is a default OGC_SERVER value in the  /var/lib/geonode/rogue_genode/geoshape/local_settings.py file. It should look like OGC_SERVER = { 'default': { 'your settings here'}}
The setting keys required for tile truncation are USER and PASSWORD. These should correspond to the username/password of your GeoServer.

Add any desired filters to the /var/lib/geonode/lib/Python27/site-packages/djfulcrum/filters file. (US geospatial and phone number filters are added by default.)
(By default these filters will be turned on, but they can be turned off in the admin console. Please be aware that the filter status changes will not be reflected in already processed data.)
(Any additional filters added must have a primary function `def filter(input)`, where input is a geojson feature collection. The filter function must return `{'passed': passed_features, 'failed': failed_features}`, where passed and failed features are geojson feature collections.)

If you have specific basemaps you would like to use, add them to the `LEAFLET_CONFIG['TILES']` array in /var/lib/geonode/rogue_geonode/geoshape/setting.py. 
Each value in the array should be a tuple where the first element is the basemap name, the second element is the basemap URL, and the third element is the atrribution. All three elements are required. 
Example: `( 'OpenStreetMap',
         'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
         'Map data &copy  <a href="http://openstreetmap.org">OpenStreetMap</a> contributors' )`
         

Finally run the command:
```
sudo geoshape-config init "geoshape.dev"
```

### custom project

First ensure you install the package:
```
python setup.py install
```

If using an existing Django Project you will need to integrate the urls and the various settings. The default settings should get you minimal functionality.  It is also assumed that you are using celery (which is recommended). If you aren't using celery it can be disabled.

If you don't have a django repo yet a script is provided with default settings that will help get you up and running.

After you installed all of the dependencies. Enter the python interpreter and enter (replacing <> with your own variable):
```
from djfulcrum.scripts.project import create_mvp
create_mvp(name=<project_name>, dir_path=<project_path>)
quit()
```

Then change directory to <project_path>/<project_name>.
Ensure you edit the <project_name>/settings.py file to the correct settings, and then run:
```
python manage.py makemigrations
python manage.py migrate
python manage.py superuser
<enter user information>
python manage.py runserver
```

## Settings

These various settings are allowed in the setting.py file for your project

####'DATABASES': (Required)
A database in which the Fulcrum data can be stored. 
Example: ```
    DATABASES = {
        'fulcrum': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': *database name*,
            'USER': *database user*,
            'PASSWORD': *database password*,
            'HOST': *database host*,
            'PORT': *database port*,
        }
    }
```

#### 'FULCRUM_UPLOAD': (Optional)
A file path where user uploaded files or S3 files will be stored while processing.
Example: `FULCRUM_UPLOAD = '/var/lib/geonode/fulcrum_data'`

#### 'S3_CREDENTIALS': (Optional)
Configuration for an S3 bucket to pull data from
Example: ```
    S3_CREDENTIALS = [{
        's3_bucket': ['my_s3_bucket'],
        's3_key': 'XXXXXXXXXXXXXXXXXXXX',
        's3_secret': 'XxXxXxXxXxXxXxXxXxXxXxX',
        's3_gpg': XxXxXxXxXxXxX'
    }]
```

       

## Known Issues
- Tiles are completely dumped when a layer is updated.  This is because the GWC bounding box tools was unsuccessful during various attempts even using their built in web tool.  This solution while inefficient is probably ok for static datasets and rarely updated data, as opposed to just not caching tiles at all.

## Bugs

Todo
