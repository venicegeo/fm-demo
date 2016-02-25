sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_layer cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_layer_id_seq cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_links cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_links_id_seq cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_asset cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_feature cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_s3 cascade"
/var/lib/geonode/bin/python /var/lib/geonode/rogue_geonode/manage.py syncdb