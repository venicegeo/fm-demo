import requests
from django.conf import settings
import gzip
from StringIO import StringIO
import xml.etree.ElementTree as ET
from geoserver.catalog import Catalog
import os
import subprocess
import shutil


def create_geogig_datastore(store_name):
    """
    Args:
        store_name: name of geogig repo

    Returns:
        None
    """

    ogc_server = get_ogc_server()
    url = "{}/rest".format(ogc_server.get('LOCATION').rstrip('/'))
    workspace_name = "geonode"
    workspace_uri = "http://www.geonode.org/"
    cat = Catalog(url)
    # Check if local workspace exists and if not create it
    workspace = cat.get_workspace(workspace_name)
    if workspace is None:
        cat.create_workspace(workspace_name, workspace_uri)
        print "Workspace " + workspace_name + " created."

    # Get list of datastores
    datastores = cat.get_stores()
    datastore = None
    # Check if remote datastore exists on local system
    for ds in datastores:
        if ds.name.lower() == store_name.lower():
            datastore = ds

    if not datastore:
        datastore = cat.create_datastore(store_name, workspace_name)
        datastore.connection_parameters.update(geogig_repository=os.path.join(ogc_server.get('GEOGIG_DATASTORE_DIR'),
                                                                              store_name))
        cat.save(datastore)


def create_geogig_repo(repo_name,
                       user_name=getattr(settings, 'SITENAME', None),
                       user_email=getattr(settings, 'SERVER_EMAIL', None)):
    repo_dir = os.path.join(get_ogc_server().get('GEOGIG_DATASTORE_DIR'), repo_name)
    if not os.path.exists(repo_dir):
        os.mkdir(repo_dir)
    if os.path.exists(os.path.join(repo_dir,'.geogig')):
        print("Cannot create new geogig repo {}, because one already exists.".format(repo_name))
        return
    prev_dir = os.getcwd()
    os.chdir(os.path.dirname(repo_dir))
    subprocess.call(['/var/lib/geogig/bin/geogig', 'init', repo_name])
    os.chdir(repo_dir)
    subprocess.call(['/var/lib/geogig/bin/geogig', 'config', 'user.name', user_name])
    subprocess.call(['/var/lib/geogig/bin/geogig', 'config', 'user.email', user_email])
    os.chdir(prev_dir)


def delete_geogig_repo(repo_name):
    repo_dir = os.path.join(get_ogc_server().get('GEOGIG_DATASTORE_DIR'), repo_name)
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)


def get_geogig_repo_name(repo):
    url = '{}'.format(get_geogig_base_url(), str(id))
    response = requests.get(url,
                            verify=False)

    pass


def get_all_geogig_repos():

    response = requests.get(get_geogig_base_url(),
                            verify=False)

    if response.status_code != 200:
        return

    root = ET.fromstring(handle_double_zip(response))

    ids = []
    for id in root.findall(".//id"):  # Returns []
        ids += [id.text]

    names = []
    for name in root.findall(".//name"):  # Returns []
        names += [name.text]

    repos={}
    for i in range(0,len(ids)):
        repos[ids[i]] = names[i]

    return repos


def get_geogig_base_url():
    """

    Returns: The full url to the geogig endpoint.

    """
    site_url = getattr(settings, 'SITEURL', None)

    ogc_server = get_ogc_server()
    if not site_url or not ogc_server:
        print("Could not find site_url or ogc_server.")
        return

    return '{}/geogig'.format((ogc_server.get('LOCATION') or site_url).strip('/'))


def handle_double_zip(response):
    """
    This can be used to handle integration issues where its possible that responses are gzipped twice.
    Args:
        response: A python requests response object.

    Returns:
        The body of the response as a string.
    """
    if response.headers.get('content-encoding') == 'gzip, gzip':
        gz_file = gzip.GzipFile(fileobj=StringIO(response.content), mode='rb')
        decompressed_file = gzip.GzipFile(fileobj=StringIO(gz_file.read()), mode='rb')
        body = decompressed_file.read()
    else:
        body = response.text
    return body


def get_ogc_server(alias=None):
    """
    Args:
        alias: An alias for which OGC_SERVER to get from the settings file, default is 'default'.

    Returns:
        A dict containing inormation about the OGC_SERVER.
    """

    ogc_server = getattr(settings, 'OGC_SERVER', None)

    if ogc_server:
        if ogc_server.get(alias):
            return ogc_server.get(alias)
        else:
            return ogc_server.get('default')