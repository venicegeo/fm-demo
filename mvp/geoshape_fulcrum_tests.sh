#!/bin/bash

#run python test cases

sudo -u postgres psql -c "alter user geoshape with superuser;"

/var/lib/geonode/bin/python /var/lib/geonode/rogue_geonode/manage.py test fulcrum_importer.tests.test_fulcrum_importer
/var/lib/geonode/bin/python /var/lib/geonode/rogue_geonode/manage.py test fulcrum_importer.tests.test_viewer
/var/lib/geonode/bin/python /var/lib/geonode/rogue_geonode/manage.py test fulcrum_importer.tests.test_tasks

sudo -u postgres psql -c "alter user geoshape with nosuperuser;"
