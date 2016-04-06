from __future__ import absolute_import
import os
import subprocess
import shutil

if os.path.exists('./db.sqlite3'):
    os.remove('./db.sqlite3')

if os.path.exists('./fulcrum_db.sqlite3'):
    os.remove('./fulcrum_db.sqlite3')

if os.path.exists('./media'):
    shutil.rmtree('./media')

if os.path.exists('./data'):
    shutil.rmtree('./data')

migration_dir = os.path.abspath('./djfulcrum/migrations')
for file_name in os.listdir(migration_dir):
    if '__init__' not in file_name.lower():
        os.remove(os.path.join(migration_dir, file_name))

subprocess.call(['python', 'manage.py', 'makemigrations'])
subprocess.call(['python', 'manage.py', 'migrate'])
subprocess.call(['python',
                 'manage.py',
                 'createsuperuser',
                 '--username',
                 'admin',
                 '--email',
                 'admin@admin.admin'])
subprocess.call(['python', 'manage.py', 'runserver'])
