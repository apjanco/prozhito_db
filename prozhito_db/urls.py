"""prozhito_db URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from prozhito_app import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomePageView.as_view(), name='HomePageView'),
    path('search/', views.SearchPageView.as_view(), name='SearchPageView'),
    #path('browse/', views.BrowsePageView.as_view(), name='BrowsePageView'),
    path('browse/<type>/', views.browse, name='browse'),
    path('chart/<entity>/', views.chart, name='chart'),
    path('export/', views.ExportPageView.as_view(), name='ExportPageView'),
    path('datatable/', views.DiariesJson.as_view(), name='diaries_json'),
    path('people-json/', views.PeopleJson.as_view(), name='people_json'),
    path('places-json/', views.PlacesJson.as_view(), name='places_json'),

]
