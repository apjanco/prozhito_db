from django.contrib.gis.db import models


# Create your models here.
class Place(models.Model):
    name = models.CharField(max_length=220, blank=True, null=True)
    wiki = models.URLField(max_length=250, blank=True)
    gis = models.PointField(null=True, blank=True)

    def __str__(self):
        return self.name


class Keyword(models.Model):
    name = models.CharField(max_length=220, blank=True, null=True)

    def __str__(self):
        return self.name


class Person(models.Model):
    id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=220, blank=True, null=True)
    patronymic = models.CharField(max_length=220, blank=True, null=True)
    family_name = models.CharField(max_length=220, blank=True, null=True)
    nickname = models.CharField(max_length=220, blank=True, null=True)
    edition = models.TextField(blank=True, null=True)
    info = models.TextField(blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)
    wiki = models.URLField(max_length=250, blank=True)
    birth_date = models.DateField()
    death_date = models.DateField()
    gender = models.CharField(max_length=220, blank=True, null=True)

    def __str__(self):
        return f'{self.lastname}, {self.firstname}, {self.patronymic}'


class Entry(models.Model):
    text = models.TextField(blank=True, null=True)
    lemmatized = models.TextField(blank=True, null=True)
    date_start = models.DateField()
    date_end = models.DateField()
    author = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name='entry_author')
    people = models.ManyToManyField(Person, blank=True, verbose_name="Person(s)")
    keywords = models.ManyToManyField(Keyword, blank=True, verbose_name="Keyword(s)")
    places = models.ManyToManyField(Place, blank=True, verbose_name="Place(s)")

    def __str__(self):
        return self.date_start

