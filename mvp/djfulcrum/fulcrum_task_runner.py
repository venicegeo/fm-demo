from __future__ import absolute_import

from hashlib import md5
from django.core.cache import cache
from multiprocessing import Process
import time
import django
from django.core.exceptions import AppRegistryNotReady
from django.db import OperationalError


class FulcrumTaskRunner:

    def __init__(self):
        name = "FulcrumTasks"
        file_name_hexdigest = md5(name).hexdigest()
        self.lock_id = '{0}-lock-{1}'.format(name, file_name_hexdigest)

    def start(self, interval=30):
        """Calls Run() sets an interval time
        Args:
            interval: An integer in seconds for the polling interval.
        """

        if cache.add(self.lock_id, True, timeout=None):
                process = Process(target=self.run, args=(interval,))
                process.daemon = True
                process.start()

    def run(self, interval):
        """Checks the 'lock' from the cache if using multiprocessing module, update if it exists.
        Args:
            interval: An integer in seconds for the polling interval.
        """
        while cache.get(self.lock_id):
            try:
                from .tasks import task_update_layers, pull_s3_data
            except AppRegistryNotReady:
                django.setup()
                from .tasks import task_update_layers, pull_s3_data
            try:
                from django.contrib.auth.models import User
                if User.objects.filter(id=1):
                    print("Updating Layers...")
                    task_update_layers()
                    print("Pulling S3 Data...")
                    pull_s3_data()
            except OperationalError as e:
                print("Database isn't ready yet.")
                print(e.message)
                print(e.args)
            time.sleep(interval)

    def stop(self):
        """Removes the 'lock' from the cache if using multiprocessing module."""
        cache.delete(self.lock_id)

    def __del__(self):
        """Used to remove the placeholder on the cache if using the multiprocessing module."""
        cache.delete(self.lock_id)
