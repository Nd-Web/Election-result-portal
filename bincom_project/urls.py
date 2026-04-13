"""
URL configuration for bincom_project.

All application routes are delegated to the elections app.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('elections.urls')),
]
