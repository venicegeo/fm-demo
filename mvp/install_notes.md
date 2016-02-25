# Copy scripts (for now just create a vagrant shared folder)
cd ~
#sudo yum install unzip -y
#wget -O demo.zip https://github.com/venicegeo/fm-demo/archive/master.zip
#unzip demo.zip
#sudo mv fm-demo-master/alerter_demo_geoshape /var/lib/demo

# Create VirtualEnv
sudo /var/lib/geonode/bin/pip install virtualenv
sudo /var/lib/geonode/bin/virtualenv /var/lib/demo/demo_env
sudo /var/lib/demo/demo_env/bin/pip install kafka-python
sudo /var/lib/demo/demo_env/bin/pip install django
sudo /var/lib/demo/demo_env/bin/pip install requests
sudo /var/lib/demo/demo_env/bin/pip install gsconfig
sudo /var/lib/demo/demo_env/bin/pip install python-dateutil
sudo /var/lib/demo/demo_env/bin/pip install fulcrum
sudo /var/lib/demo/demo_env/bin/pip install celery
#wget -O pyscopg2.tar.gz https://pypi.python.org/packages/source/p/psycopg2/psycopg2-2.6.1.tar.gz#md5=842b44f8c95517ed5b792081a2370da1
#tar -zxvf pyscopg2.tar.gz
#cd psycopg2-2.6.1
# /var/lib/demo/demo_env/bin/python setup.py install --pg-config /usr/pgsql-9.5/bin/pg_config
# ln -s /var/lib/geonode/lib/python2.7/site-packages/celery /var/lib/demo/demo_env/lib/python2.7/site-packages/celery
# ln -s /var/lib/geonode/lib/python2.7/site-packages/kombu /var/lib/demo/demo_env/lib/python2.7/site-packages/kombu
# ln -s /var/lib/geonode/lib/python2.7/site-packages/billiard /var/lib/demo/demo_env/lib/python2.7/site-packages/billiard
# ln -s /var/lib/geonode/lib/python2.7/site-packages/amqp /var/lib/demo/demo_env/lib/python2.7/site-packages/amqp
# ln -s /var/lib/geonode/lib/python2.7/site-packages/anyjson /var/lib/demo/demo_env/lib/python2.7/site-packages/anyjson
# ln -s /var/lib/geonode/lib/python2.7/site-packages/binascii /var/lib/demo/demo_env/lib/python2.7/site-packages/binascii
# ln -s /var/lib/geonode/lib/python2.7/site-packages/five /var/lib/demo/demo_env/lib/python2.7/site-packages/five

#ln -s /etc/geoshape/local_settings.py /var/lib/demo/demo_app/local_settings.py

# Install Django, Requests, kafka-python
sudo -u postgres /usr/bin/psql -c "CREATE DATABASE fulcrum WITH OWNER geoshape;"
sudo -u postgres /usr/bin/psql -d "fulcrum" -c "CREATE EXTENSION postgis;"
sudo geoshape-config updatelayers

# Run demo
cd /var/lib/demo
sudo chown -R geoshape:geoservice /var/lib/demo
sudo -u geoshape /var/lib/demo/demo_env/bin/python ./initialize.py
