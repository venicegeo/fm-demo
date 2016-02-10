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

from django import forms

class ListenerForm(forms.Form):
    listener_topic = forms.CharField(label='Listener Topic', max_length=100)
    listener_key = forms.CharField(label='Listener Key', max_length=100)

class UploadFulcrumData(forms.Form):
    file = forms.FileField()
