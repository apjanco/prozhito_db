from prozhito_app.models import *
from django.db.models import Q
import time
from prozhito_app import generate_keywords_from_statement_list

from itertools import chain


def advanced_search(request):

    # right now it looks like [Iraq-Any Field-Iran-OR-Keyword-]
    # so we split on - and delete the last one (there is always a tailing empty list
    request_list = request.GET["full_info"].split("-")[:-1]

    # request list needs to be split into threes
    # right now it looks like ['Iraq','','Any Field', 'Iran', 'OR', 'Keyword,...]
    # note that the first one will not have the logical operator
    start = time.time()
    formatted_request_list = []
    ticker = 1
    three_pair = {}
    for item in request_list:
        if ticker == 1:
            three_pair["search_string"] = item
        elif ticker == 2:
            three_pair["logic"] = item
        elif ticker == 3:
            three_pair["field"] = item
            formatted_request_list.append(three_pair)
            three_pair = {}
            ticker = 0  # set to zero since we are going inc after
        ticker += 1

    query = False
    for request_part in formatted_request_list:
        search_string = request_part["search_string"]
        logic = request_part["logic"]
        field = request_part["field"]

        queryset = make_queryset(search_string, field)

        if query and queryset:
            if logic == "AND":
                query = query & queryset
            elif logic == "OR":
                query = query | queryset
            elif logic == "NOT":
                query = query - queryset
        elif queryset:
            query = queryset
        else:
            return False

    result_list = list(query)
    q_time = time.time() - start
    print("generating result_list took %s seconds" % q_time)
    context = {
        'results': result_list,
        'search': search_string,
        'full_info': request.GET["full_info"],
        'num_results': len(result_list),
    }
    return context


def make_queryset(search_string, field):  # this will return queryset in SET
    if field == "любом поле":
        # return Entry, Place, Person objects.
        q1 = set(
            Person.objects.filter(
                Q(first_name__icontains=search_string)
                | Q(patronymic__icontains=search_string)
                | Q(family_name__icontains=search_string)
            )
        )
        q2 = set(Place.objects.filter(name__icontains=search_string))
        # it is still a question whether there is a need to return Imagen objects
        q3 = set(
            Entry.objects.filter(
                Q(lemmatized_icontains=search_string)
            )
        )
        queryset = q1 | q2 | q3
        # print('queryset', queryset)
    elif field == 'людях':
        q1 = set(Person.objects.filter(
            Q(first_name__icontains=search_string)
            | Q(patronymic__icontains=search_string)
            | Q(family_name__icontains=search_string)
            ))
        
        queryset = q1

    elif field == 'местах':
        q1 = set(Place.objects.filter(name__icontains=search_string))
        queryset = q1

    elif field == 'записях':
        queryset = set(Entry.objects.filter(lemmatized__icontains=search_string))
    
    else:
        print("Found an invalid field.")
        print("If you've just updated the field options dropdown,")
        return False
    return queryset


def make_query_part(search_string, field):
    print(field)
    if field == "любом поле":
        query_part = Q(
            # Q(persona__nombre_de_la_persona__icontains=search_string) |
            # Q(carpeta__descripción__icontains=search_string) |
            Q(ubicación_geográfica__nombre_del_lugar__icontains=search_string)
            | Q(género__icontains=search_string)
            | Q(etnicidad__icontains=search_string)
            | Q(texto_de_OCR__icontains=search_string)
        )
    elif field == 'людях':
        query_part = Q(person__family_name__icontains=search_string)
    elif field == 'местах':
        query_part = Q(place__name__icontains=search_string)
    elif field == 'записях':
        query_part = Q(entry__lemmatized__icontains=search_string)
    else:
        print("Found an invalid field.")
        print("If you've just updated the field options dropdown,")
        print("go and update 'make_query_part' in 'advanced_search.py'")
        return False
    return query_part


# used for filtering
def advanced_search_make_query(request):
    request_list = request.GET["full_info"].split(",")

    # request list needs to be split into threes
    # right now it looks like ['Iraq','','Any Field', 'Iran', 'OR', 'Keyword,...]
    # note that the first one will not have the logical operator
    formatted_request_list = []
    ticker = 1
    three_pair = {}
    for item in request_list:
        if ticker == 1:
            three_pair["search_string"] = item
        elif ticker == 2:
            three_pair["logic"] = item
        elif ticker == 3:
            three_pair["field"] = item
            formatted_request_list.append(three_pair)
            three_pair = {}
            ticker = 0  # set to zero since we are going inc after
        ticker += 1

    query = []
    for request_part in formatted_request_list:
        search_string = request_part["search_string"]
        logic = request_part["logic"]
        field = request_part["field"]
        query_part = make_query_part(search_string, field)
        if query and query_part:
            if logic == "AND":
                query = query & query_part
            elif logic == "OR":
                query = query | query_part
            elif logic == "NOT":
                query = query & ~query_part
        elif query_part:
            query = query_part
        else:
            return False

    return query