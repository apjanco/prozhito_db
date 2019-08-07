from django.contrib import admin
from prozhito_app.models import *
# Register your models here.
from django.contrib.gis import admin
from mapwidgets.widgets import GooglePointFieldWidget


class PersonAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'patronymic', 'family_name',]
    list_filter = ['from_tags', 'from_natasha']

admin.site.register(Person, PersonAdmin)


class PlaceAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }

admin.site.register(Place, PlaceAdmin)


class EntryAdmin(admin.ModelAdmin):
    search_fields = ['id', ]
    list_filter = ['sentiment']
    autocomplete_fields = ['people',]


admin.site.register(Entry, EntryAdmin)

class KeywordAdmin(admin.ModelAdmin):
    pass

admin.site.register(Keyword, KeywordAdmin)
