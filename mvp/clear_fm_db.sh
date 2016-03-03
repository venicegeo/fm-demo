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
sudo -u geoshape psql -d geoshape_data -c "drop table test cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table test2 cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table test3 cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey_business cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey_business_pic_business cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey_business_pic_marketing cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey_pic_bldg cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table urban_survey_pic_utility cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table cemetery_survey cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table cemetery_survey_photos_cemetery cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table cemetery_survey_plot_photo cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table commodities_survey_photos cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table educational_facilities_survey cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table educational_facilities_survey_photos cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table emergency_services_survey cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table emergency_services_survey_photos cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table fuel_survey cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table fuel_survey_photos cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table graffiti_survey cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table graffiti_survey_photos cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table networks cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table political_groups_campaigns cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table political_groups_campaigns_photos cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table production_facility cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table production_facility_photos cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table production_facility_product_photos_1 cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table production_facility_product_photos_2 cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table utilities_assessment_data cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table utilities_assessment_data_photos cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table vehicle_survey cascade"
sudo -u geoshape psql -d geoshape_data -c "drop table vehicle_survey_vehicle_photos cascade"

#restart service
service geoshape restart
