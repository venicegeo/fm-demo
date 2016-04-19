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

from __future__ import absolute_import

from django.contrib import admin
from .models import S3Credential, S3Bucket, FulcrumApiKey, Filter, FilterGeneric, FilterArea, TextFilter
from django.contrib import messages

class S3BucketInline(admin.TabularInline):
    model = S3Bucket


class S3Admin(admin.ModelAdmin):
    inlines = [
        S3BucketInline
    ]

    fieldsets = (
        (None, {
            'fields': ('s3_description', 's3_key', 's3_secret', 's3_gpg'),
            'description': "Enter S3 Credentials for a bucket(s) which contain one or more zipfiles of Fulcrum data."
        }),
    )


class FilterGenericInline(admin.TabularInline):
    model = FilterGeneric
    can_delete = True


class FilterAreaInline(FilterGenericInline):
    model = FilterArea
    extra = 0
   # readonly_fields = ('filter_area_name',)
    fieldsets = (
        (None, {
            'fields': ('filter_area_enabled',
                       'filter_area_name',
                       'filter_area_buffer',
                       'filter_area_data'),
            'description': "Data can be excluded through filters or included."
        }),
    )


class FilterAdmin(admin.ModelAdmin):
    readonly_fields = ('filter_name', 'filter_previous_status')
    exclude = ('filter_previous_time',)
    model = Filter
    fieldsets = (
        (None, {
            'fields': ('filter_name', 'filter_previous_status', 'filter_active', 'filter_inclusion', 'filter_previous'),
            'description': "Filters are DESTRUCTIVE, points cannot be recovered if filtered.  Filters are applied to ALL layers."
        }),
    )

    def save_model(self, request, obj, form, change):
        if obj.is_filter_running():
            messages.error(request, "The filter settings cannot be changed while filtering is in progress. \n"
                                    "The current changes have not been saved.")
        else:
            super(FilterAdmin, self).save_model(request, obj, form, change)

    def get_inline_instances(self, request, obj=None):
        inline_instances = []

        if obj.filter_name == 'geospatial_filter.py':
            inlines = [FilterAreaInline]
        else:
            inlines = []

        for inline_class in inlines:
            inline = inline_class(self.model, self.admin_site)
            if request:
                if not (inline.has_add_permission(request) or
                            inline.has_change_permission(request) or
                            inline.has_delete_permission(request)):
                    continue
                if not inline.has_add_permission(request):
                    inline.max_num = 0
            inline_instances.append(inline)
        return inline_instances

    def get_formsets(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            yield inline.get_formset(request, obj)


admin.site.register(S3Credential, S3Admin)
admin.site.register(FulcrumApiKey)
# admin.site.register(FilterArea)
admin.site.register(Filter, FilterAdmin)
