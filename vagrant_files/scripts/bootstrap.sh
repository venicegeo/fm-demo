#!/usr/bin/env bash

# exit if anything returns failure
set -e

yum -y install http://yum.geoshape.org/geoshape-repo-0.0.1-0.1beta.el6.noarch.rpm
yum -y install geoshape

mkfs.ext4 -F /dev/sdb
echo "/dev/sdb                /var/lib/geoserver_data/file-service-store ext4 defaults 1 2" >> /etc/fstab
mount -a
chown tomcat:geoservice /var/lib/geoserver_data/file-service-store
chmod 775 /var/lib/geoserver_data/file-service-store