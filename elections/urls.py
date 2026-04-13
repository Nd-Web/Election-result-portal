"""
URL patterns for the elections app.
"""

from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('polling-unit/', views.PollingUnitResultsView.as_view(), name='polling_unit'),
    path('lga-results/', views.LgaResultsView.as_view(), name='lga_results'),
    path('add-result/', views.AddResultView.as_view(), name='add_result'),
]
