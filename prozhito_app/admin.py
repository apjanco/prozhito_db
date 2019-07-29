from django.contrib import admin
from prozhito_app.models import *
# Register your models here.
from django.contrib.gis import admin
from mapwidgets.widgets import GooglePointFieldWidget


class PersonAdmin(admin.ModelAdmin):
    search_fields = ['firstname', 'patronymic', 'lastname',]

admin.site.register(Person, PersonAdmin)


class PlaceAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }

admin.site.register(Place, PlaceAdmin)


class EntryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Entry, EntryAdmin)

class KeywordAdmin(admin.ModelAdmin):
    pass

admin.site.register(Keyword, KeywordAdmin)
