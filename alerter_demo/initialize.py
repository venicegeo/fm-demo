import os, glob, subprocess

if os.path.isfile('./db.sqlite3'):
    os.remove('./db.sqlite3')
for filename in glob.glob("./alerts/migrations/*"):
    if '__init__' not in filename:
        os.remove(filename)

subprocess.call(['python','manage.py','makemigrations'])
subprocess.call(['python','manage.py','migrate'])
subprocess.call(['python','manage.py','runserver'])