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
from django.http import JsonResponse
import pickle
from prozhito_app import advanced_search
from django.http import HttpResponse
from dal import autocomplete
from django.shortcuts import redirect

def make_dict(**args):  # Used to create a dictionary of the current state
    return args

def update_state(request):
    request.session['query'] = request.POST.get('query', None)
    request.session['people'] = request.POST.get('people', None)
    request.session['places'] = request.POST.get('places', None)
    request.session['keywords'] = request.POST.get('keywords', None)
    request.session['start_year'] = request.POST.get('start_year', None)
    request.session['end_year'] = request.POST.get('end_year', None)
    
def get_state(request):
    query = request.session.get('query')
    people = request.session.get('people')
    places = request.session.get('places')
    keywords = request.session.get('keywords')
    start_year = request.session.get('start_year')
    end_year = request.session.get('end_year')

    state = make_dict(query=query, people=people, places=places, keywords=keywords, start_year=start_year,
                      end_year=end_year)
    return state

def home(request):
    if request.method == 'POST':
        update_state(request)
        return redirect('table/diaries')
    
    else:
        return render(request, 'index.html', )


def table(request, type):
    if request.method == 'POST':
        # Update state with the current search request
        update_state(request)

        # Get the current state variable to pass on to the template 
        state = get_state(request)
        context = {'state': state}
        return render(request, 'table.html', context)

    else:
        state = get_state(request)
        context = {'state': state}
        return render(request, 'table.html', context)


def map(request, entity):
    if request.method == 'POST':
        # Update state with the current search request
        update_state(request)

        # Get the current state variable to pass on to the template 
        state = get_state(request)

        context = {'state': state }
        if entity == 'diaries':
            entries = Entry.objects.filter(~Q(places=None))
            if state['query'] != '':
                entries = entries.filter(Q(text__icontains=state['query']))

            if state['start_year'] or state['end_year']:
                start_year = f'{state["start_year"]}-01-01'

                end_year = f'{state["end_year"]}-12-31'

                dates = Q(date_start__gte=start_year) & Q(date_start__lte=end_year)
                entries = entries.filter(dates)

            #entries = Entry.objects.filter(~Q(places=None) & Q(date_start__gte=start_year) & Q(date_start__lte=end_year))
            # TODO Good place for a pickle
            places = [entry.places.all() for entry in entries]
            all_places = set({})
            for place in places:
                for i in place:
                    all_places.add(i)
            # For this map, what's most helpful is not places (which will equal all places), but frequency of entries per place
            context['places'] = places
    
        if entity == 'people':
            context = {}
    
        if entity == 'places':
            places = Place.objects.all()
            context['places'] = places

        if entity == 'entries':
            entries = Entry.objects.filter(~Q(places=None) & Q(date_start__gte=start_year) & Q(date_start__lte=end_year))
            entries = entries.filter(Q(text__icontains=query))
            # TODO Good place for a pickle
            places = [entry.places.all() for entry in entries]
            all_places = set({})
            for place in places:
                for i in place:
                    all_places.add(i)
            #For this map, what's most helpful is not places (which will equal all places), but frequency of entries per place
            context['places']= places

        return render(request, 'map.html', context)

    else:
        state = get_state(request)

        context = {'state': state}

        if entity == 'diaries':
            entries = Entry.objects.filter(~Q(places=None))
            if state['query'] != '':
                entries = entries.filter(Q(text__icontains=state['query']))

            if state['start_year'] or state['end_year']:
                start_year = f'{state["start_year"]}-01-01'

                end_year = f'{state["end_year"]}-12-31'

                dates = Q(date_start__gte=start_year) & Q(date_start__lte=end_year)
                entries = entries.filter(dates)

            places = [entry.places.all() for entry in entries]
            all_places = set({})
            for place in places:
                for i in place:
                    all_places.add(i)
            # For this map, what's most helpful is not places (which will equal all places), but frequency of entries per place
            context['places'] = all_places

        if entity == 'people':
            context = {}

        if entity == 'places':
            places = Place.objects.all()
            context['places'] = places

        if entity == 'entries':
            entries = Entry.objects.filter(~Q(places=None))
            if query:
                entries = entries.filter(Q(text__icontains=query))

            if start_year or end_year:
                try:
                    start_year = '{}-01-01'.format(start_year)
                except django.core.exceptions.ValidationError:
                    pass

                try:
                    end_year = '{}-12-31'.format(end_year)
                except django.core.exceptions.ValidationError:
                    pass

                dates = Q(date_start__gte=start_year) & Q(date_start__lte=end_year)
                entries = entries.filter(dates)

            places = [entry.places.all() for entry in entries]
            all_places = set({})
            for place in places:
                for i in place:
                    all_places.add(i)
            # For this map, what's most helpful is not places (which will equal all places), but frequency of entries per place
            context['places'] = all_places

        return render(request, 'map.html', context)



def chart(request, entity):
    
    if request.method == 'POST':
        # Update state with the current search request
        update_state(request)

        # Get the current state variable to pass on to the template
        state = get_state(request)

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
            context = {'graph':div, 'state': state}

        return render(request, 'chart.html', context)

    else:
        state = get_state(request)
        context = {'state': state}

        if entity == 'entries':
            layout = go.Layout(
                title="<b>Количество записей в дневнике по месяцам и годам</b>",
                xaxis={'title': 'год'}, yaxis={'title': 'количество'},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)')

            figure = go.Figure(layout=layout)

            qs = pickle.load(open("/srv/prozhito_db/prozhito_app/entry_date_count.pickle", "rb"))
            # qs = Entry.objects.order_by().values('date_start').distinct().annotate(Count('date_start'))
            x = [q['date_start'] for q in qs]
            y = [q['date_start__count'] for q in qs]

            figure.add_trace(go.Scatter(x=x, y=y, mode="markers", marker=dict(
                color='#E4653F',
                size=5),
                                        ))

            div = opy.plot(figure, auto_open=False, output_type='div')
            context = {'graph': div}

        if entity == 'people':
            layout = go.Layout(
                title="<b>Количество упоминаний человека по фамилии</b>",
                xaxis={'title': 'фамилия'}, yaxis={'title': 'количество'},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)')

            figure = go.Figure(layout=layout)

            qs = Entry.objects.order_by('people__family_name').values('people__family_name').distinct().annotate(
                Count('people__family_name'))
            x = [q['people__family_name'] for q in qs]
            y = [q['people__family_name__count'] for q in qs]

            figure.add_trace(go.Scatter(x=x, y=y, mode="markers", marker=dict(
                color='#E4653F',
                size=5),
                                        ))

            div = opy.plot(figure, auto_open=False, output_type='div')
            context = {'graph': div}

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
            context = {'graph': div}

        if entity == 'diaries':
            layout = go.Layout(
                title="<b>Количество записей в дневнике по автору</b>",
                xaxis={'title': 'автор', 'showticklabels': False, }, yaxis={'title': 'количество'},
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
            context = {'graph': div, 'state': state}

        return render(request, 'chart.html', context)


def export(request):
    if request.method == 'POST':
        # Update state with the current search request
        update_state(request)

        # Get the current state variable to pass on to the template
        state = get_state(request)

        context = {'state': state,}
        return render(request, 'export.html', context)

    else:
        state = get_state(request)
        context = {'state': state,}
        return render(request, 'export.html', context)


def export_state(request):
    state = get_state(request)
    from django.core import serializers
    if state['start_year'] is None or state['end_year'] is None:
        entries = serializers.serialize("json",
                                        Entry.objects.filter(
                                            Q(date_start__gte=''.join(['1681', '-01', '-01']))
                                            & Q(date_start__lte=''.join(['2018', '-01', '-01']))))

    else:
        entries = serializers.serialize("json",
                                        Entry.objects.filter(Q(date_start__gte=''.join([state['start_year'], '-01', '-01']))
                                                             & Q(date_start__lte=''.join([state['end_year'], '-01', '-01']))))

    return JsonResponse(entries, safe=False)

class EntryJson(BaseDatatableView):
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
            return format_html("""
            {}<button type="button" class="btn btn-default" style="color: #ea6645;" data-toggle="modal" data-target="#aaa{}">...открыть</button>
            
            <!-- Modal -->
            <div class="modal fade" id="aaa{}" tabindex="-1" role="dialog" aria-labelledby="exampleModalLongTitle" aria-hidden="true">
              <div class="modal-dialog" role="document">
                <div class="modal-content" style="width: 100%">
                  <div class="modal-header">
                    <h5 class="modal-title" id="exampleModalLongTitle">{}. {}</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                      <span aria-hidden="true">&times;</span>
                    </button>
                  </div>
                  <div class="modal-body">
                    {}
                  </div>
                  <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">...закрыть</button>
                  </div>
                </div>
              </div>
            </div>
            
            """.format(formatter(row.text[:150], filter_name='markdown'), row.id, row.id, row.date_start, row.author, formatter(row.text, filter_name='markdown')))

        if column == 'date_start':
            return format_html("<p>{}</p>".format(row.date_start,))
        if column == 'author':
            return format_html("<p>{}</p>".format(row.author,))
        if column == 'keywords':
            return format_html("<p>{}</p>".format([keyword.name for keyword in row.keywords.all()],))
        if column == 'author':
            return format_html("<p>{}</p>".format(row.sentiment,))

        else:
            return super(EntryJson, self).render_column(row, column)

    def filter_queryset(self, qs):
        # use parameters passed in GET request to filter queryset
        query = self.request.session.get('query')
        people = self.request.session.get('people')
        start_year = self.request.session.get('start_year')
        end_year = self.request.session.get('end_year')

        if people:
            print(int(people))
            q = Q(people__id__in=[int(people)]) | Q(author__in=[int(people)])
            qs = qs.filter(q)

        if start_year or end_year:
            try:
                start_year = '{}-01-01'.format(start_year)
            except django.core.exceptions.ValidationError:
                pass
            print('start_year=', start_year)

            try:
                end_year = '{}-12-31'.format(end_year)
            except django.core.exceptions.ValidationError:
                pass
            print('end_year=', end_year)

            dates = Q(date_start__gte=start_year)|Q(date_start__isnull=True) & Q(date_start__lte=end_year)|Q(date_start__isnull=True)
            qs = qs.filter(dates)

        if query:
            q = Q(text__icontains=query) #| Q(date_start__icontains=search) | Q(author__first_name__icontains=search) | Q(sentiment__icontains=search)
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
    columns = ['family_name', 'first_name', 'patronymic', 'info', 'birth_date', 'death_date'] # 'info', 'birthday', 'deathday', 'wikilink']

    # define column names that will be used in sorting
    # order is important and should be same as order of columns displayed by datatables
    # for non sortable columns use empty value like ''
    order_columns = ['family_name','first_name', 'patronymic', 'info', 'birth_date', 'death_date'] # 'info', 'birthday', 'deathday', 'wikilink']

    # set max limit of records returned
    # this is used to protect your site if someone tries to attack your site and make it return huge amount of data
    max_display_length = 500


    def render_column(self, row, column):
        # we want to render 'translation' as a custom column, because 'translation' is defined as a Textfield in Image model,
        # but here we only want to check the status of translating process.
        # so, if 'translation' is empty, i.e. no one enters any information in 'translation', we display 'waiting';
        # otherwise, we display 'processing'.
        if column == 'family_name':
            return format_html("<p>{}</p>".format(row.family_name,))
        if column == 'patronymic':
            return format_html("<p>{}</p>".format(row.patronymic,))
        if column == 'first_name':
            return format_html("<p>{}</p>".format(row.first_name,))
        if column == 'info':
            return format_html("<p>{}</p>".format(row.info,))
        if column == 'birth_date':
            return format_html("<p>{}</p>".format(row.birth_date,))
        if column == 'death_date':
            return format_html("<p>{}</p>".format(row.death_date,))
        else:
            return super(PeopleJson, self).render_column(row, column)

    def filter_queryset(self, qs):

        query = self.request.session.get('query')
        people = self.request.session.get('people')
        
        start_year = self.request.session.get('start_year')
        end_year = self.request.session.get('end_year')
        if start_year or end_year:
            try:
                start_year = '{}-01-01'.format(start_year)
            except django.core.exceptions.ValidationError:
                pass
            
            try:
                end_year = '{}-12-31'.format(end_year)
            except django.core.exceptions.ValidationError:
                pass
            dates = Q(birth_date__gte=start_year)| Q(birth_date__isnull=True) & Q(death_date__lte=end_year)|Q(death_date__isnull=True)
            qs = qs.filter(dates)

        if query:
            q = Q(info__icontains=query) | Q(first_name__icontains=query) | Q(family_name__icontains=query)
            qs = qs.filter(q)
        
        if people:
            print(people, "it's peoples!")
            q = Q(id=int(people))
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
    columns = ['name', 'wiki', 'date', 'geom',] # 'info', 'birthday', 'deathday', 'wikilink']

    # define column names that will be used in sorting
    # order is important and should be same as order of columns displayed by datatables
    # for non sortable columns use empty value like ''
    order_columns = ['name', 'wiki', 'date', 'geom',] # 'info', 'birthday', 'deathday', 'wikilink']

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
        #if column == 'date':
        #    return format_html("<p>{}</p>".format(['<a href="">{}-{}-{}</a>'.format(i.date_start.year, i.date_start.month, i.date_start.day) for i in Entry.objects.filter(places=row.id)]))

        if column == 'date':
            html = ''
            entry = Entry.objects.filter(places=row.id)
            for i in entry:
                line = f"""<button type="button" class="btn btn-default" style="color: #ea6645;" data-toggle="modal" data-target="#aaa{i.id}">{i.date_start.year}-{i.date_start.month}-{i.date_start.day}</button>
                        <!-- Modal -->
                        <div class="modal fade" id="aaa{i.id}" tabindex="-1" role="dialog" aria-labelledby="exampleModalLongTitle" aria-hidden="true">
                          <div class="modal-dialog" role="document">
                            <div class="modal-content" style="width: 100%">
                              <div class="modal-header">
                                <h5 class="modal-title" id="exampleModalLongTitle">{i.date_start.year}-{i.date_start.month}-{i.date_start.day}. {i.author}</h5>
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                  <span aria-hidden="true">&times;</span>
                                </button>
                              </div>
                              <div class="modal-body">
                                {formatter(i.text, filter_name='markdown')}
                              </div>
                              <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">...закрыть</button>
                              </div>
                            </div>
                          </div>
                        </div>
                        """
                html += line

            return format_html(html)

        if column == 'geom':
            try:
                return format_html("<p>{},{}</p>".format(row.geom.x, row.geom.y))
            except AttributeError:
                return format_html("<p></p>")

        else:
            return super(PlacesJson, self).render_column(row, column)

    def filter_queryset(self, qs):
        # use parameters passed in GET request to filter queryset
        query = self.request.session.get('query')
        people = self.request.session.get('people')
        start_year = self.request.session.get('start_year')
        end_year = self.request.session.get('end_year')
        places = self.request.session.get('places')

        #qs = Entry.objects.filter(places__id__in=[places])

        if people:
            q = Q(entry__people__id__in=[int(people)]) | Q(entry__author__in=[int(people)])
            qs = qs.filter(q)

        if start_year or end_year:
            try:
                start_year = '{}-01-01'.format(start_year)
            except django.core.exceptions.ValidationError:
                pass
            print('start_year=', start_year)

            try:
                end_year = '{}-12-31'.format(end_year)
            except django.core.exceptions.ValidationError:
                pass
            print('end_year=', end_year)

            dates = Q(entry__date_start__gte=start_year)|Q(entry__date_start__isnull=True) & Q(entry__date_start__lte=end_year)|Q(entry__date_start__isnull=True)
            qs = qs.filter(dates)

        if query:
            q = Q(name__icontains=query) #| Q(date_start__icontains=search) | Q(author__first_name__icontains=search) | Q(sentiment__icontains=search)
            qs = qs.filter(q)
        #qs = [entry.places.all()[0] for entry in qs]  #Note the [0], this will need to be changed when select2 multi is working
        return qs.distinct()


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
            return format_html("<a href='http://prozhito.org/person/{}' target='_blank'>{}</a>".format(row.author.id, row.author,))
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
        query = self.request.session.get('query')
        people = self.request.session.get('people')
        places = self.request.session.get('places')
        keywords = self.request.session.get('keywords')
        start_year = self.request.session.get('start_year')
        end_year = self.request.session.get('end_year')

        if people:
            print(people)
            q = Q(author=int(people))

            qs = qs.filter(q)
            print('people', len(qs))
        
        if start_year or end_year:
            try:
                start_year = '{}-01-01'.format(start_year)
            except django.core.exceptions.ValidationError:
                start_year = None
            print('start_year=', start_year)
            
            try:
                end_year = '{}-12-31'.format(end_year)
            except django.core.exceptions.ValidationError:
                end_year = None
            print('end_year=', end_year)


            dates = Q(first_note__gte=start_year)|Q(first_note__isnull=True) & Q(last_note__lte=end_year)|Q(last_note__isnull=True)
            qs = qs.filter(dates)
            print('dates', len(qs))
        
        if query:
            q = Q(author__first_name__icontains=query) | Q(author__patronymic__icontains=query) | \
                Q(author__family_name__icontains=query)
            
            qs = qs.filter(q)
            print('query', len(qs))
            
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

