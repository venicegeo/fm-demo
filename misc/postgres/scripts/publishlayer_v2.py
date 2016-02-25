from geoserver.catalog import Catalog
import os

localDSObj = None
localDSName = None
localURL="http://localhost:8080/geoserver/rest"
localWSObj = None
localWSName = "geonode"
localWSURI = "http://www.geonode.org/"
localLayerName = None
remoteDSName = "piazza_postgis"
remoteHost="192.168.99.111"
remotePort="5432"
remoteDatabase="geoshape_data"
remoteUser="geoshape"
remotePassword="SIDsH9CWhKWGRGhS"
remoteDBType="postgis"
remoteLayerName="virginia_natural"
WGS84="EPSG:4326"

cat = Catalog(localURL)

# Check if local workspace exists and if not create it 
localWSObj = cat.get_workspace (localWSName)

if localWSObj is None:
    localWSObj = cat.create_workspace(localWSName, localWSURI)
    print "Workspace " + localWSName + " created"
else:
    print "Workspace " + localWSName + " already exists" 

# Get list of datastores
dataStoresObj = cat.get_stores()

# Check if remote datastore exists on local system
for dataStoreObj in dataStoresObj:
    if dataStoreObj.name == remoteDSName:
        localDSObj = dataStoreObj
        print "Datastore " + localDSObj.name + " already exists"

if not localDSObj:
    localDSObj = cat.create_datastore(remoteDSName, localWSName)     
    localDSObj.connection_parameters.update(host=remoteHost, port=remotePort, \
        database=remoteDatabase, user=remoteUser, passwd=remotePassword, dbtype=remoteDBType)
    cat.save(localDSObj)
    print "Datastore " + localDSObj.name + " created"

# Check if remote layer already exists on local system
localLayersObj = cat.get_layers()

for localLayerObj in localLayersObj:
    if localLayerObj.resource.name == remoteLayerName:
        localLayerName = remoteLayerName
        print "Layer " + remoteLayerName + " already published"

if not localLayerName:
    # Publish remote layer    
    featureType = cat.publish_featuretype(remoteLayerName, localDSObj, WGS84, srs=WGS84)
    print "Published layer " + remoteLayerName
    
    # Update layers in GeoSHAPE
    os.system("sudo geoshape-config updatelayers")


