# Copy scripts (for now just create a vagrant shared folder)
cd ~
sudo yum install unzip -y
wget -O demo.zip https://github.com/venicegeo/fm-demo/archive/geoshape_demo.zip
unzip demo.zip
sudo mv fm-demo-geoshape_demo/alerter_demo_geoshape /var/lib/demo

# Create VirtualEnv
/var/lib/geonode/bin/pip install virtualenv
/var/lib/geonode/bin/virtualenv /var/lib/demo/demo_env
/var/lib/demo/demo_env/bin/pip install kafka-python
/var/lib/demo/demo_env/bin/pip install django
/var/lib/demo/demo_env/bin/pip install requests
/var/lib/demo/demo_env/bin/pip install gsconfig
/var/lib/demo/demo_env/bin/pip install python-dateutil
/var/lib/demo/demo_env/bin/pip install fulcrum

ln -s /etc/geoshape/local_settings.py /var/lib/demo/demo_app/local_settings.py

# Install Django, Requests, kafka-python
sudo -u postgres /usr/bin/psql -c "CREATE DATABASE fulcrum WITH OWNER geoshape;"
sudo -u postgres /usr/bin/psql -d "fulcrum" -c "CREATE EXTENSION postgis;"
sudo geoshape-config updatelayers

# Run demo
cd /var/lib/demo
sudo chown -R geoshape:geoservice /var/lib/demo
sudo -u geoshape /var/lib/demo/demo_env/bin/python ./initialize.py
