"""alerts URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from . import views
from django.conf import settings
from django.conf.urls.static import static

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^pz_fulcrum_geojson$',views.geojson),
    url(r'^pz_fulcrum_map$',views.viewer),
    url(r'^pz_fulcrum_viewer$',views.viewer),
    url(r'^pz_fulcrum_upload$',views.upload),
    url(r'^pz_fulcrum_layers$',views.layers),
    url(r'^pz_fulcrum_pzworkflow$', views.pzworkflow),
    url(r'^pz_fulcrum_pzmodels$', views.pz_models)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

