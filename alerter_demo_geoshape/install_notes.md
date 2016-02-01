# Copy scripts (for now just create a vagrant shared folder)

# Create VirtualEnv
/var/lib/geoshape/bin/pip install virtualenv
/var/lib/geoshape/bin/virtualenv /var/lib/demo/demo_env
/var/lib/demo/demo_env/bin/pip install kafka-python
/var/lib/demo/demo_env/bin/pip install django
/var/lib/demo/demo_env/bin/pip install requests

# Install Django, Requests, kafka-python
sudo -u postgres /usr/bin/psql -c "CREATE DATABASE fulcrum WITH OWNER geoshape;"
sudo -u postgres /usr/bin/psql -d "fulcrum" -c "CREATE EXTENSION postgis;"
sudo geoshape-config updatelayers

# Run demo
cd /var/lib/demo
sudo -U geoshape /var/lib/demo/demo_env/bin/python ./initialize.py