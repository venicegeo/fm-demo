#Geoshape-Fulcrum MVP

This is a django application which allows the user to connect to a kafka server and ingest data. If the data is a valid geojson feature it can be displayed on a map.

## Requirements

 - Geoshape-Vagrant 
 
## Setup 

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
wget https://raw.githubusercontent.com/venicegeo/fm-mvp/master/mvp/geoshape_fulcrum_install.sh -O- | tr -d '\r' > /tmp/geoshape_fulcrum_install.sh
sudo bash /tmp/geoshape_fulcrum_install.sh
```

By default the install script should take care of the following dependencies:
```
/var/lib/geonode/bin/pip install fulcrum
/var/lib/geonode/bin/pip install python-memcached
/var/lib/geonode/bin/pip install boto3
/var/lib/geonode/bin/pip install Pillow
```

You can modify your fulcrum api key entry in /var/lib/geonode/rogue_geonode/geoshape/local_settings.py
 file (sudo required).
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

 .  The name of an S3 bucket should be provided as well.  If the bucket is s3://my-data then the value should be S3_BUCKET = "my-data".
 
To allow for geoshape tile truncation on addition of new data, make sure there is a default OGC_SERVER value in the  /var/lib/geonode/rogue_genode/geoshape/local_settings.py file. It should look like OGC_SERVER = { 'default': { 'your settings here'}}
The setting keys required for tile truncation are USER and PASSWORD. These should correspond to the username/password of your GeoServer.

Add any desired filters to the /var/lib/geonode/rogue_geonode/geoshape/local_settings.py file. (US geospatial and phone number filters are added by default.)
(By default these filters will be turned on, but they can be turned off in the admin console. Please be aware that the filter status changes will not be reflected in already processed data.)
(Any additional filters added must have a primary function `def filter(input)`, where input is a geojson feature collection. The filter function must return `{'passed': passed_features, 'failed': failed_features}`, where passed and failed features are geojson feature collections.)

Finally run the command:
```
sudo geoshape-config init "geoshape.dev"
```

##Known Issues

- Sometimes duplicate points are allowed in the same layer.
- Tiles are completely dumped when a layer is updated.  This is because the GWC bounding box tools was unsuccessful during various attempts even using their built in web tool.  This solution while inefficient is probably ok for static datasets and rarely updated data, as opposed to just not caching tiles at all.
- Unit tests need to be done.
- An installer should be created.

## Bugs

Todo
