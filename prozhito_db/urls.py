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
    path('', views.home, name='home'),
    path('table/<type>/', views.table, name='table'),
    path('chart/<entity>/', views.chart, name='chart'),
    path('map/<entity>/', views.map, name='map'),
    path('export/', views.export, name='export'),
    ]

urlpatterns += [
    path('entry-json/', views.EntryJson.as_view(), name='entry_json'),
    path('diary-json/', views.DiaryJson.as_view(), name='diary_json'),
    path('people-json/', views.PeopleJson.as_view(), name='people_json'),
    path('places-json/', views.PlacesJson.as_view(), name='places_json'),
    path('person-autocomplete/', views.PersonAutocomplete.as_view(), name='person-autocomplete'),
    path('place-autocomplete/', views.PlaceAutocomplete.as_view(), name='place-autocomplete'),
    path('keyword-autocomplete/', views.KeywordAutocomplete.as_view(), name='keyword-autocomplete'),
]
