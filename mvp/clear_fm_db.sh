pkill -f supervisord && pkill -f celery

sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_layer cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_layer_id_seq cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_links cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_links_id_seq cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_asset cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_feature cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_s3 cascade"
sudo -u geoshape psql -d geoshape -c "drop table fulcrum_importer_s3sync cascade"
/var/lib/geonode/bin/python /var/lib/geonode/rogue_geonode/manage.py syncdb


# Delete all of the layer links in geoshape
sudo -u geoshape psql -d geoshape -c "drop table layers_layer cascade"
/var/lib/geonode/bin/python /var/lib/geonode/rogue_geonode/manage.py syncdb

# Delete data
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey_business cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey_business_pic_business cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey_business_pic_marketing cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey_pic_bldg cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey_pic_utility cascade"

#restart service
service geoshape restart
