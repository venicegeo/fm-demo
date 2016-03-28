import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

setup(
    name='fm-mvp',
    version='1.0.0',
    author='Radiant Blue',
    author_email='venice@radiantblue.com',
    url='https://github.com/venicegeo/fm-mvp',
    download_url="https://github.com/venicegeo/fm-mvp",
    description="Ingest Fulcrum data to django app",
    long_description=open(os.path.join(here, 'README.md')).read(),
    license='See LICENSE file.',
    packages=find_packages(exclude=["mvp"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=['fulcrum', 'python-memcached', 'boto3', 'Pillow', 'django'],
    classifiers=['Topic :: Utilities',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Intended Audience :: Developers',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Development Status :: 1 - Planning',
                 'Programming Language :: Python :: 2.7'],
)
