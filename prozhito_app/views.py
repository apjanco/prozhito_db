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


class HomePageView(TemplateView):

    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = Entry.objects.all()[:5]
        return context

    def update_project_state(request):
        current_state = 'put state here'
        request.session['project_state'] = current_state

    def update_state(request):
        current_state = request.session.get('project_state')

class SearchPageView(TemplateView):

    template_name = "search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = Entry.objects.all()[:5]
        return context


class BrowsePageView(TemplateView):

    template_name = "browse.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = Entry.objects.all()[:5]
        return context


def browse(request, type):
    
    return render(request, 'browse.html',)

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
    columns = ['text', 'date_start', 'author'] # 'info', 'birthday', 'deathday', 'wikilink']

    # define column names that will be used in sorting
    # order is important and should be same as order of columns displayed by datatables
    # for non sortable columns use empty value like ''
    order_columns =  ['text', 'date_start','author'] # 'info', 'birthday', 'deathday', 'wikilink']

    # set max limit of records returned
    # this is used to protect your site if someone tries to attack your site and make it return huge amount of data
    max_display_length = 500

    def render_column(self, row, column):
        # we want to render 'translation' as a custom column, because 'translation' is defined as a Textfield in Image model,
        # but here we only want to check the status of translating process.
        # so, if 'translation' is empty, i.e. no one enters any information in 'translation', we display 'waiting';
        # otherwise, we display 'processing'.
        if column == 'текст':
            return format_html("<p>{}</p>".format(formatter(row.text, filter_name='markdown')))
        if column == 'date_start':
            return format_html("<p>{}</p>".format(row.date_start,))
        if column == 'author':
            return format_html("<p>{}</p>".format(row.author,))

        else:
            return super(DiariesJson, self).render_column(row, column)

    def filter_queryset(self, qs):
        # use parameters passed in GET request to filter queryset

        # here is a simple example
        search = self.request.GET.get('search[value]', None)
        if search:
            q = Q(text__icontains=search) | Q(date_start__icontains=search) | Q(author__icontains=search)
            qs = qs.filter(q)
        return qs
