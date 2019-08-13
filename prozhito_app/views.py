from django.shortcuts import render
from django.views.generic.base import TemplateView
from prozhito_app.models import *
import plotly.offline as opy
import plotly.graph_objs as go
from django.db.models import Count
from django.core import serializers
from django.utils.html import escape, format_html, mark_safe
from django_markup.markup import formatter
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.db.models import Q
import pickle
from prozhito_app import advanced_search
from django.http import HttpResponse
from dal import autocomplete
from django.shortcuts import redirect


def home(request):
    if request.method == 'POST':
        request.session['query'] = request.POST.get('query', None)
        request.session['people'] = request.POST.get('people', None)
        request.session['places'] = request.POST.get('places', None)
        request.session['keywords'] = request.POST.get('keywords', None)
        request.session['start_year'] = request.POST.get('start_year', None)
        request.session['end_year'] = request.POST.get('end_year', None)
        return redirect('table/diaries')
    else:
        return render(request, 'index.html', )


def search(request):

    query = request.session.get('query')
    people = request.session.get('people')
    places = request.session.get('places')
    entries = request.session.get('entries')
    start_year = request.session.get('start_year')
    end_year = request.session.get('end_year')
    print(query, people, places, entries, start_year, end_year)
    return render(request, 'search.html', )


def table(request, type):
    if request.method == 'POST':
        query = request.POST.get('query', None)
        people = request.POST.get('people', None)
        places = request.POST.get('places', None)
        keywords = request.POST.get('keywords', None)
        start_year = request.POST.get('start_year', None)
        end_year = request.POST.get('end_year', None)
        print(query, people, places, keywords, start_year, end_year)

        return render(request, 'table.html', )

    else:
        query = request.session.get('query')
        people = request.session.get('people')
        places = request.session.get('places')
        keywords = request.session.get('keywords')
        start_year = request.session.get('start_year')
        end_year = request.session.get('end_year')
        print(query, people, places, keywords, start_year, end_year)
        return render(request, 'table.html',)

def map(request, entity):

    if entity == 'diaries':
        context = {}

    if entity == 'people':
        context = {}

    if entity == 'places':
        places = Place.objects.all()
        context = {'places': places}


    if entity == 'entries':
        entries = Entry.objects.filter(~Q(places=None))
        # TODO Good place for a pickle
        places = [entry.places.all() for entry in entries]
        all_places = set({})
        for place in places:
            for i in place:
                all_places.add(i)
        #For this map, what's most helpful is not places (which will equal all places), but frequency of entries per place
        context = {'places':places}


    return render(request, 'map.html', context)


def chart(request, entity):
    if entity == 'entries':
        layout = go.Layout(
            title="<b>Количество записей в дневнике по месяцам и годам</b>",
            xaxis={'title': 'год'}, yaxis={'title': 'количество'},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)')

        figure = go.Figure(layout=layout)
        
        qs = pickle.load(open("/srv/prozhito_db/prozhito_app/entry_date_count.pickle", "rb"))
        #qs = Entry.objects.order_by().values('date_start').distinct().annotate(Count('date_start'))
        x = [q['date_start'] for q in qs]
        y = [q['date_start__count'] for q in qs]

        figure.add_trace(go.Scatter(x=x, y=y, mode="markers", marker=dict(
            color='#E4653F',
            size=5),
                                    ))

        div = opy.plot(figure, auto_open=False, output_type='div')
        context = {'graph':div}

    if entity == 'people':
        layout = go.Layout(
            title="<b>Количество упоминаний человека по фамилии</b>",
            xaxis={'title': 'фамилия'}, yaxis={'title': 'количество'},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)')

        figure = go.Figure(layout=layout)

        qs = Entry.objects.order_by('people__family_name').values('people__family_name').distinct().annotate(Count('people__family_name'))
        x = [q['people__family_name'] for q in qs]
        y = [q['people__family_name__count'] for q in qs]

        figure.add_trace(go.Scatter(x=x, y=y, mode="markers", marker=dict(
            color='#E4653F',
            size=5),
                                    ))

        div = opy.plot(figure, auto_open=False, output_type='div')
        context = {'graph':div}

    if entity == 'places':
        layout = go.Layout(
            title="<b>Количество упоминаний места</b>",
            xaxis={'title': 'места'}, yaxis={'title': 'количество'},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)')

        figure = go.Figure(layout=layout)

        qs = Entry.objects.order_by('places__name').values('places__name').distinct().annotate(Count('places__name'))
        x = [q['places__name'] for q in qs]
        y = [q['places__name__count'] for q in qs]

        figure.add_trace(go.Scatter(x=x, y=y, mode="markers", marker=dict(
            color='#E4653F',
            size=5),
                                    ))

        div = opy.plot(figure, auto_open=False, output_type='div')
        context = {'graph':div}

    if entity == 'diaries':
        layout = go.Layout(
            title="<b>Количество записей в дневнике по автору</b>",
            xaxis={'title': 'автор', 'showticklabels':False,}, yaxis={'title': 'количество'},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)')

        figure = go.Figure(layout=layout)

        qs = Diary.objects.all().order_by('no_entries')
        x = [' '.join([str(q.author.first_name), str(q.author.patronymic), str(q.author.family_name)]) for q in qs]
        y = [q.no_entries for q in qs]

        figure.add_trace(go.Scatter(x=x, y=y, mode="markers", marker=dict(
            color='#E4653F',
            size=5),
                                    ))

        div = opy.plot(figure, auto_open=False, output_type='div')
        context = {'graph':div}

    return render(request, 'chart.html', context)


class ExportPageView(TemplateView):

    template_name = "export.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = Entry.objects.all()[:5]
        return context



class DiariesJson(BaseDatatableView):
    # the model you're going to show
    model = Entry

    """
    id = models.AutoField(primary_key=True)
    text = models.TextField(blank=True, null=True)
    lemmatized = models.TextField(blank=True, null=True)
    date_start = models.DateField(blank=True, null=True)
    date_end = models.DateField(blank=True, null=True)
    author = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name='entry_author')
    people = models.ManyToManyField(Person, blank=True, verbose_name="Person(s)")
    keywords = models.ManyToManyField(Keyword, blank=True, verbose_name="Keyword(s)")
    places = models.ManyToManyField(Place, blank=True, verbose_name="Place(s)")
    diary = models.IntegerField(default=None)
    sentiment = models.CharField(max_length=220, blank=True, null=True)

    """

    # define columns that will be returned
    # they should be the fields of your model, and you may customize their displaying contents in render_column()
    # don't worry if your headers are not the same as your field names, you will define the headers in your template
    columns = ['text', 'date_start', 'author', 'keywords', 'sentiment'] # 'info', 'birthday', 'deathday', 'wikilink']

    # define column names that will be used in sorting
    # order is important and should be same as order of columns displayed by datatables
    # for non sortable columns use empty value like ''
    order_columns =  ['text', 'date_start','author', 'keywords', 'sentiment'] # 'info', 'birthday', 'deathday', 'wikilink']

    # set max limit of records returned
    # this is used to protect your site if someone tries to attack your site and make it return huge amount of data
    max_display_length = 500

    def render_column(self, row, column):
        # we want to render 'translation' as a custom column, because 'translation' is defined as a Textfield in Image model,
        # but here we only want to check the status of translating process.
        # so, if 'translation' is empty, i.e. no one enters any information in 'translation', we display 'waiting';
        # otherwise, we display 'processing'.
        if column == 'text':
            return format_html("<p>{}</p>".format(formatter(row.text, filter_name='markdown')))
        if column == 'date_start':
            return format_html("<p>{}</p>".format(row.date_start,))
        if column == 'author':
            return format_html("<p>{}</p>".format(row.author,))
        if column == 'keywords':
            return format_html("<p>{}</p>".format([keyword.name for keyword in row.keywords.all()],))
        if column == 'author':
            return format_html("<p>{}</p>".format(row.sentiment,))

        else:
            return super(DiariesJson, self).render_column(row, column)

    def filter_queryset(self, qs):
        # use parameters passed in GET request to filter queryset

        # here is a simple example
        search = self.request.GET.get('search[value]', None)
        if search:
            q = Q(text__icontains=search) | Q(date_start__icontains=search) | Q(author__first_name__icontains=search) | Q(sentiment__icontains=search)
            qs = qs.filter(q)
        return qs


class PeopleJson(BaseDatatableView):
    # the model you're going to show
    model = Person

    """
   id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=220, blank=True, null=True)
    patronymic = models.CharField(max_length=220, blank=True, null=True)
    family_name = models.CharField(max_length=220, blank=True, null=True)
    nickname = models.CharField(max_length=220, blank=True, null=True)
    edition = models.TextField(blank=True, null=True)
    info = models.TextField(blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)
    wiki = models.URLField(max_length=1000, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    death_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=220, blank=True, null=True)
    from_natasha = models.BooleanField(default=False)
    from_tags = models.BooleanField(default=False)
    """

    # define columns that will be returned
    # they should be the fields of your model, and you may customize their displaying contents in render_column()
    # don't worry if your headers are not the same as your field names, you will define the headers in your template
    columns = ['first_name', 'patronymic', 'family_name', 'info', 'birth_date',] # 'info', 'birthday', 'deathday', 'wikilink']

    # define column names that will be used in sorting
    # order is important and should be same as order of columns displayed by datatables
    # for non sortable columns use empty value like ''
    order_columns = ['first_name', 'patronymic', 'family_name', 'info', 'birth_date',] # 'info', 'birthday', 'deathday', 'wikilink']

    # set max limit of records returned
    # this is used to protect your site if someone tries to attack your site and make it return huge amount of data
    max_display_length = 500

    def render_column(self, row, column):
        # we want to render 'translation' as a custom column, because 'translation' is defined as a Textfield in Image model,
        # but here we only want to check the status of translating process.
        # so, if 'translation' is empty, i.e. no one enters any information in 'translation', we display 'waiting';
        # otherwise, we display 'processing'.
        if column == 'text':
            return format_html("<p>{}</p>".format(row.first_name,))
        if column == 'patronymic':
            return format_html("<p>{}</p>".format(row.patronymic,))
        if column == 'author':
            return format_html("<p>{}</p>".format(row.family_name,))
        if column == 'info':
            return format_html("<p>{}</p>".format(row.info,))
        if column == 'birth_date':
            return format_html("<p>{}</p>".format(row.birth_date,))
        else:
            return super(PeopleJson, self).render_column(row, column)

    def filter_queryset(self, qs):
        # use parameters passed in GET request to filter queryset

        # here is a simple example
        search = self.request.GET.get('search[value]', None)
        if search:
            q = Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(info__icontains=search)
            qs = qs.filter(q)
        return qs


class PlacesJson(BaseDatatableView):
    # the model you're going to show
    model = Place

    """
    name = models.CharField(max_length=220, blank=True, null=True)
    wiki = models.URLField(max_length=250, blank=True)
    gis = models.PointField(null=True, blank=True)
    """

    # define columns that will be returned
    # they should be the fields of your model, and you may customize their displaying contents in render_column()
    # don't worry if your headers are not the same as your field names, you will define the headers in your template
    columns = ['name', 'wiki', 'geom',] # 'info', 'birthday', 'deathday', 'wikilink']

    # define column names that will be used in sorting
    # order is important and should be same as order of columns displayed by datatables
    # for non sortable columns use empty value like ''
    order_columns = ['name', 'wiki', 'geom',] # 'info', 'birthday', 'deathday', 'wikilink']

    # set max limit of records returned
    # this is used to protect your site if someone tries to attack your site and make it return huge amount of data
    max_display_length = 500

    def render_column(self, row, column):
        # we want to render 'translation' as a custom column, because 'translation' is defined as a Textfield in Image model,
        # but here we only want to check the status of translating process.
        # so, if 'translation' is empty, i.e. no one enters any information in 'translation', we display 'waiting';
        # otherwise, we display 'processing'.
        if column == 'name':
            return format_html("<p>{}</p>".format(row.name,))
        if column == 'wiki':
            return format_html("<p>{}</p>".format(row.wiki,))
        if column == 'geom':
            try:
                return format_html("<p>{},{}</p>".format(row.geom.x, row.geom.y))
            except AttributeError:
                return format_html("<p></p>")

        else:
            return super(PlacesJson, self).render_column(row, column)

    def filter_queryset(self, qs):
        # use parameters passed in GET request to filter queryset

        # here is a simple example
        search = self.request.GET.get('search[value]', None)
        if search:
            q = Q(name__icontains=search) | Q(wiki__icontains=search)
            qs = qs.filter(q)
        return qs

class DiaryJson(BaseDatatableView):
    # the model you're going to show
    model = Diary

    """
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name='diary_author')
    no_entries = models.IntegerField(default=None)
    first_note = models.DateField(blank=True, null=True)
    last_note = models.DateField(blank=True, null=True)

    """

    # define columns that will be returned
    # they should be the fields of your model, and you may customize their displaying contents in render_column()
    # don't worry if your headers are not the same as your field names, you will define the headers in your template
    columns = ['author', 'no_entries', 'first_note', 'last_note',] # 'info', 'birthday', 'deathday', 'wikilink']

    # define column names that will be used in sorting
    # order is important and should be same as order of columns displayed by datatables
    # for non sortable columns use empty value like ''
    order_columns = ['author', 'no_entries', 'first_note', 'last_note',] # 'info', 'birthday', 'deathday', 'wikilink']

    # set max limit of records returned
    # this is used to protect your site if someone tries to attack your site and make it return huge amount of data
    max_display_length = 500

    def render_column(self, row, column):
        # we want to render 'translation' as a custom column, because 'translation' is defined as a Textfield in Image model,
        # but here we only want to check the status of translating process.
        # so, if 'translation' is empty, i.e. no one enters any information in 'translation', we display 'waiting';
        # otherwise, we display 'processing'.
        if column == 'author':
            return format_html("<p>{}</p>".format(row.author,))
        if column == 'no_entries':
            return format_html("<p>{}</p>".format(row.no_entries,))
        if column == 'first_note':
            return format_html("<p>{}</p>".format(row.first_note,))
        if column == 'last_note':
            return format_html("<p>{}</p>".format(row.last_note, ))

        else:
            return super(DiaryJson, self).render_column(row, column)

    def filter_queryset(self, qs):
        # use parameters passed in GET request to filter queryset

        # here is a simple example
        search = self.request.GET.get('search[value]', None)
        if search:
            q = Q(author__first_name__icontains=search) | Q(author__patronymic__icontains=search) | Q(author__family_name__icontains=search)
            qs = qs.filter(q)
        return qs

class PersonAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):


        qs = Person.objects.all()



        if self.q:
            search = self.q
            q = Q(first_name__icontains=search) | Q(patronymic__icontains=search) | Q(family_name__icontains=search)
            qs = qs.filter(q)


        return qs

class PlaceAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):

        qs = Place.objects.all()

        if self.q:
            q = Q(name__icontains=self.q)
            qs = qs.filter(q)


        return qs

class KeywordAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):

        qs = Keyword.objects.all()

        if self.q:
            q = Q(name__icontains=self.q)
            qs = qs.filter(q)


        return qs
