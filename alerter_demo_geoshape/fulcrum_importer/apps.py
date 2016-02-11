# Copyright 2016, RadiantBlue Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import unicode_literals

from django.apps import AppConfig


class FulcrumImporterConfig(AppConfig):
    name = 'fulcrum_importer'

    def ready(self):
        from django.db.utils import OperationalError
        try:
            from .models import Layer
            from geoshape_fulcrum import Fulcrum_Importer
            print("Server loaded.")
            fulcrum = Fulcrum_Importer()
            fulcrum.start()
        except OperationalError:
            print("Data has not yet been migrated.")
            exit(0)

