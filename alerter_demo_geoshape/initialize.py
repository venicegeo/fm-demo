import os, glob, subprocess

if os.path.isfile('./db.sqlite3'):
    os.remove('./db.sqlite3')
for filename in glob.glob("./fulcrum_importer/migrations/*"):
    if '__init__' not in filename:
        os.remove(filename)

python_bin = '/var/lib/demo/demo_env/bin/python'
subprocess.call([python_bin,'manage.py','makemigrations'])
subprocess.call([python_bin,'manage.py','migrate'])
subprocess.call([python_bin,'manage.py','runserver','0.0.0.0:8004'])