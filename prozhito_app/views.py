from django.shortcuts import render
from django.views.generic.base import TemplateView
from prozhito_app.models import *

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

class ExportPageView(TemplateView):

    template_name = "export.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = Entry.objects.all()[:5]
        return context