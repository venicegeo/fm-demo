from __future__ import absolute_import

from celery import shared_task

from .fulcrum_importer import FulcrumImporter
@shared_task(name="fulcrum_importer.tasks.print_test")
def print_test(data):
    print("Test success: {}.".format(data))

@shared_task(name="fulcrum_importer.tasks.task_update_layers")
def task_update_layers():
    fulcrum_importer = FulcrumImporter()
    fulcrum_importer.update_all_layers()