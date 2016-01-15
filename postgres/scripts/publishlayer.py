from geoserver.catalog import Catalog
datastore_found = False

cat = Catalog("http://localhost:8080/geoserver/rest")

ws = cat.get_workspace ("geonode")
if ws is None:
    ws = cat.create_workspace("geonode", "http://www.geonode.org/")

ds = None

all_stores = cat.get_stores()
for store in all_stores:
    if store.name == "piazza_postgis":
        ds = store

if not ds:
    ds = cat.create_datastore("piazza_postgis", "geonode")     
    ds.connection_parameters.update(host='192.168.99.111', port='5432', database='geoshape_data', user='geoshape', passwd='SIDsH9CWhKWGRGhS', dbtype='postgis')
    cat.save(ds)
    print "Datastore " + ds.name + " created"
    
ft = cat.publish_featuretype("virginia_natural", ds, 'EPSG:4326', srs='EPSG:4326')
print ft.enabled
